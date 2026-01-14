import curses
import enum

import colors
import commands
import controls
import executor
from entities.context import AppContext
from entities.request import Collection, Request
import util

from views.request_view import RequestView
from views.response_view import ResponseView


class Mode(enum.Enum):
    control = 0
    command = 1


class App:
    __stdscr: curses.window

    __mode: Mode
    __running: bool

    # UI
    __collection_pane: controls.Panel
    __collection: controls.ListBox
    __command: controls.LineEdit

    __request_pane: controls.Panel

    __focus: controls.Control | None

    # Internal
    __executor: executor.RequestExecutor

    # Public
    context: AppContext

    def __init__(self, stdscr: curses.window):
        self.__stdscr = stdscr
        self.__mode = Mode.control
        self.__running = True
        self.context = AppContext.create()

        bounds = stdscr.getmaxyx()

        controls.Control.configure(foreground=colors.parse_color(self.context.settings.colors.foreground), background=colors.parse_color(self.context.settings.colors.background))
        stdscr.bkgd(colors.color_pair(
            colors.parse_color(self.context.settings.colors.foreground),
            colors.parse_color(self.context.settings.colors.background)
        ))
        stdscr.refresh()

        self.__collection_pane = controls.Panel(stdscr, (0, 0), (bounds[0] - 2, 50))
        pane_size = self.__collection_pane.pane_size
        self.__collection_name = controls.Label(self.__collection_pane.window, (1, 1), (1, pane_size[1]))
        self.__collection_name.bold = True
        self.__collection_name.italic = True
        self.__collection_name.underline = True
        self.__collection = controls.ListBox(self.__collection_pane.window, (2, 1), (pane_size[0] - 1, pane_size[1]))

        pane_width = (bounds[1] - 50) // 2
        self.__request_pane = RequestView(self, (0, 50), (bounds[0] - 2, pane_width))
        self.__response_pane = ResponseView(self,(0, 50 + pane_width), (bounds[0] - 2, pane_width))

        self.__status  = controls.Label(stdscr, (bounds[0] - 2, 0), (1, bounds[1]))
        self.__status.background = colors.parse_color(self.context.settings.colors.contrast)
        self.__status.foreground = colors.parse_color(self.context.settings.colors.foreground)
        self.__command = controls.LineEdit(stdscr, (bounds[0] - 1, 0), bounds[1])

        self.__focus = None
        self.__executor = executor.RequestExecutor()

        self.create_collection("Unsorted Collection", True)

        # renders
        self.__request_pane.repaint()
        self.__response_pane.repaint()
        self.__collection_name.repaint()
        self.__collection.repaint()
        self.__status.repaint()

    def update_focus(self):
        if self.__focus is not None and not self.__focus.focused:
            self.__focus = None

    def set_focus(self, focus: controls.Control | None):
        if self.__focus is not None:
            self.__focus.unfocus()

        if focus:
            try:
                focus.focus()
                self.__focus = focus
            except controls.CannotFocus:
                self.__focus = None

    def run(self) -> int:
        curses.curs_set(0)
        self.__stdscr.nodelay(True)
        while self.__running:
            ch = self.__stdscr.getch()
            if ch == 27:
                next = self.__stdscr.getch()
                if next != -1:
                    continue
            elif ch == -1:
                self.update_focus()
                continue

            if self.__mode == Mode.control:
                can_take_focus = self.__focus is None or (self.__focus is not None and not self.__focus.focus_greedy)
                if ch == ord(':') and can_take_focus:
                    self.begin_command()
                elif self.__focus is not None:
                    self.__focus.handle_input(ch)
                else:
                    self.__request_pane.handle_input(ch)
            else:
                if ch == ord('\n'):
                    self.execute_command()
                elif ch == 27:
                    self.cancel_command()
                else:
                    curses.curs_set(2)
                    self.update_command(ch)
                    command = self.__command.get_text()
                    if not command.startswith(':'):
                        self.cancel_command()

        return 0

    def begin_command(self):
        self.__mode = Mode.command
        self.__command.set_text(":")
        self.__command.focus()
        curses.curs_set(2)

    def cancel_command(self):
        curses.curs_set(0)
        self.__mode = Mode.control
        self.__command.set_text("")
        self.__command.unfocus()

    def execute_command(self):
        curses.curs_set(0)
        self.__mode = Mode.control
        command = self.__command.get_text()
        self.__command.set_text("")
        self.__command.unfocus()
        try:
            commands.execute(command, self)
            self.status_clear()
        except commands.CommandError as err:
            self.status_error("Error: " + str(err))

    def update_command(self, ch: int):
        self.__command.handle_input(ch)

    # convenience status functions
    def status_error(self, message: str):
        with self.__status.no_repaint():
            self.__status.set_text(message)
            self.__status.bold = True
            self.__status.italic = True
            self.__status.foreground = colors.parse_color(self.context.settings.colors.error)

    def status_info(self, message: str):
        with self.__status.no_repaint():
            self.__status.set_text(message)
            self.__status.bold = False
            self.__status.italic = False
            self.__status.foreground = colors.parse_color(self.context.settings.colors.foreground)

    def status_clear(self):
        with self.__status.no_repaint():
            self.__status.bold = False
            self.__status.italic = False
            self.__status.underline = False
            self.__status.set_text("")

    # public API
    def create_collection(self, name: str, activate: bool = False) -> Collection:
        new_collection = Collection(requests=[], name=name)
        self.context.collections.append(new_collection)
        if activate:
            self.set_active_collection(new_collection)
        return new_collection

    def set_active_collection(self, collection: Collection):
        self.context.active_collection = collection
        self.__collection_pane.window.move(1, 1)
        length = self.__collection_pane.pane_size[1]
        self.__collection_name.set_text(util.ellipsize(collection.name, length).ljust(length, " "))
        self.__collection.clear()
        for request in collection.requests:
            self.__collection.add_item(request.name)

    def set_active_request(self, request: Request):
        pass

    def create_request(self, name: str, activate: bool = False) -> Request:
        if self.context.active_collection is None:
            raise ValueError("No active collection.")

        if name in [request.name for request in self.context.active_collection.requests]:
            raise commands.CommandError("Request '%s' already exists in this collection." % name)

        new_request = Request(name=name, method="POST", url="http://httpbin.org/get", headers={})
        self.context.active_collection.requests.append(new_request)
        self.__collection.insort_item(name, key=str.lower)
        if activate:
            self.set_active_request(new_request)
        return new_request

    def execute_request(self):
        if self.context.active_collection and self.context.active_request:
            exec_id = f"{self.context.active_collection.name}/{self.context.active_request.name}"
            self.__executor.dispatch(self.context.active_request, exec_id)

    def quit(self):
        self.__running = False

    @property
    def stdscr(self) -> curses.window:
        return self.__stdscr

