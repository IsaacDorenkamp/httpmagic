import curses
import enum
import uuid

import httpx

import colors
import commands
import controls
import executor
from entities.context import AppContext
from entities.request import Collection, Request
from entities.response import Response
import util

from persist import PersistStore
from views.request_view import RequestView
from views.response_view import ResponseView


class Mode(enum.Enum):
    control = 0
    command = 1


class App:
    __stdscr: curses.window

    __store: PersistStore

    __mode: Mode
    __running: bool

    # UI
    __collection_pane: controls.Panel
    __collection: controls.ListBox
    __command: controls.LineEdit

    __request_pane: RequestView
    __response_pane: ResponseView

    __focus: controls.Control | None

    # Internal
    __executor: executor.RequestExecutor

    # Public
    context: AppContext

    def __init__(self, stdscr: curses.window, context: AppContext, store: PersistStore):
        self.__stdscr = stdscr
        self.__store = store
        self.__mode = Mode.control
        self.__running = True
        self.context = context

        bounds = stdscr.getmaxyx()

        controls.Control.configure(foreground=colors.get_color("foreground"), background=colors.get_color("background"))
        stdscr.bkgd(colors.color_pair(
            colors.get_color("foreground"),
            colors.get_color("background"),
        ))
        stdscr.refresh()

        self.__collection_pane = controls.Panel(stdscr, (0, 0), (bounds[0] - 2, 50))
        pane_size = self.__collection_pane.pane_size
        self.__collection_name = controls.Label(self.__collection_pane.window, (1, 1), (1, pane_size[1]))
        self.__collection_name.bold = True
        self.__collection_name.italic = True
        self.__collection_name.underline = True
        self.__collection = controls.ListBox(self.__collection_pane.window, (2, 1), (pane_size[0] - 1, pane_size[1]))
        self.__collection.change = self._request_changed

        pane_width = (bounds[1] - 50) // 2
        self.__request_pane = RequestView(self, (0, 50), (bounds[0] - 2, pane_width))
        self.__request_pane.set_content_visible(False)
        self.__response_pane = ResponseView(self,(0, 50 + pane_width), (bounds[0] - 2, pane_width))

        self.__status  = controls.Label(stdscr, (bounds[0] - 2, 0), (1, bounds[1]))
        self.__status.background = colors.get_color("contrast")
        self.__status.foreground = colors.get_color("foreground")
        self.__command = controls.LineEdit(stdscr, (bounds[0] - 1, 0), bounds[1])

        self.__focus = None
        self.__executor = executor.RequestExecutor()

        if self.context.collections:
            collection = self.context.collections[0]
            self.set_active_collection(collection)
            if collection.requests:
                self.set_active_request(collection.requests[0])

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

    def update(self):
        for request_key, result in self.__executor.collect():
            if isinstance(result, httpx.Response):
                self.set_response(request_key, Response(status=result.status_code, headers=dict(result.headers), data=result.content))

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
                self.update()
                continue

            if self.__mode == Mode.control:
                can_take_focus = self.__focus is None or (self.__focus is not None and not self.__focus.focus_greedy)
                if ch == ord(':') and can_take_focus:
                    self.begin_command()
                elif self.__focus is not None:
                    self.__focus.handle_input(ch)
                elif ch == controls.Control.CTRL_S:
                    self.set_focus(self.__collection)
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

            self.update()

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
            self.__status.foreground = colors.get_color("error")

    def status_info(self, message: str):
        with self.__status.no_repaint():
            self.__status.set_text(message)
            self.__status.bold = False
            self.__status.italic = False
            self.__status.foreground = colors.get_color("foreground")

    def status_clear(self):
        with self.__status.no_repaint():
            self.__status.bold = False
            self.__status.italic = False
            self.__status.underline = False
            self.__status.set_text("")

    # public API
    def set_response(self, request_key: str, response: Response):
        self.context.responses[request_key] = response
        if request_key == self.active_request_key:
            self.__response_pane.set_response(response)

    def create_collection(self, name: str, activate: bool = False) -> Collection:
        new_collection_id = uuid.uuid4()
        # TODO: validate uniqueness of id
        new_collection = Collection(id=new_collection_id, requests=[], name=name)
        self.store.save_collection(new_collection)
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
        self.context.active_request = request
        self.__request_pane.set_method(request.method)
        self.__request_pane.set_url(request.url)
        self.__request_pane.set_content_visible(True)

    def create_request(self, name: str, activate: bool = False) -> Request:
        if self.context.active_collection is None:
            raise ValueError("No active collection.")

        if name in [request.name for request in self.context.active_collection.requests]:
            raise ValueError("Request '%s' already exists in this collection." % name)

        new_request = Request(name=name, method="GET", url="http://httpbin.org/get", headers={})
        self.store.save_request(self.store.get_collection_root(self.context.active_collection), new_request)
        self.context.active_collection.requests.append(new_request)
        self.__collection.insort_item(name, key=str.lower, select=True)
        if activate:
            self.set_active_request(new_request)
        return new_request

    def rename_active_request(self, name: str):
        if self.context.active_request is None or self.context.active_collection is None:
            raise ValueError("Not active request.")
        elif self.context.active_request.name == name:
            raise ValueError("Name was not changed!")

        existing = next((request for request in self.context.active_collection.requests if request.name == name), None)
        if existing is not None:
            raise ValueError("A request named '%s' already exists in this collection." % name)

        index = self.__collection.find(self.context.active_request.name)
        if index >= 0:
            self.__collection.set_item(index, name, resort=str.lower)
            new_index = self.__collection.find(name)
            self.context.active_request.name = name
            self.__collection.set_selection(new_index)
        else:
            raise ValueError("Request '%s' does not exist in the current collection." % self.context.active_request.name)

    def rename_active_collection(self, name: str):
        if self.context.active_collection is None:
            raise ValueError("No collection is active.")
        elif name == self.context.active_collection.name:
            raise ValueError("Name was not changed!")

        existing = next((collection for collection in self.context.collections if collection.name == name), None)
        if existing is not None:
            raise ValueError("A collection named '%s' already exists." % name)

        self.context.active_collection.name = name
        self.__collection_name.set_text(name.ljust(self.__collection_pane.pane_size[1], " "))


    def execute_request(self):
        exec_id = self.active_request_key
        if exec_id and self.context.active_request:
            self.__response_pane.set_loading(True)
            self.__executor.dispatch(self.context.active_request, exec_id)

    def quit(self):
        self.__running = False

    # change listeners
    def _request_changed(self, request_name: str | None):
        if self.context.active_collection is None:
            return

        if request_name is None:
            self.__request_pane.set_content_visible(False)
        else:
            request = next((request for request in self.context.active_collection.requests if request.name == request_name), None)
            if request is not None:
                self.set_active_request(request)

    # properties
    @property
    def active_request_key(self) -> str | None:
        if self.context.active_collection and self.context.active_request:
            return f"{self.context.active_collection.name}/{self.context.active_request.name}"

        return None

    @property
    def stdscr(self) -> curses.window:
        return self.__stdscr

    @property
    def store(self) -> PersistStore:
        return self.__store

