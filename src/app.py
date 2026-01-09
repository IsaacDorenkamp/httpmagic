import curses
import enum
import string

import controls
from entities.context import AppContext
from entities.request import Collection
import util


class Mode(enum.Enum):
    control = 0
    command = 1


class App:
    __stdscr: curses.window

    __mode: Mode
    __running: bool

    __collection: controls.ListBox
    __command: controls.LineEdit

    __focus: controls.Control | None

    context: AppContext

    def __init__(self, stdscr: curses.window):
        self.__stdscr = stdscr
        self.__mode = Mode.control
        self.__running = True

        bounds = stdscr.getmaxyx()

        self.__collection_pane = controls.Panel(stdscr, (0, 0), (bounds[0] - 1, 25))
        self.__collection = controls.ListBox(self.__collection_pane.window, (1, 1), self.__collection_pane.pane_size)

        for letter in string.ascii_uppercase:
            self.__collection.add_item(letter)

        self.__command = controls.LineEdit(stdscr, (bounds[0] - 1, 1), bounds[1] - 1)

        self.__focus = None
        self.context = AppContext.create()

        self.set_focus(self.__collection)

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
        while self.__running:
            ch = self.__stdscr.getch()
            if self.__mode == Mode.control:
                if ch == ord('!'):
                    self.begin_command()
                elif ch == ord('+'):
                    self.create_collection("New Collection")
                elif self.__focus is not None:
                    self.__focus.handle_input(ch)
            else:
                if ch == ord('\n'):
                    self.execute_command()
                else:
                    self.update_command(ch)
                    command = self.__command.get_text()
                    if not command.startswith('!'):
                        self.cancel_command()

        return 0

    def begin_command(self):
        self.__mode = Mode.command
        self.__command.set_text("!")

    def cancel_command(self):
        self.__mode = Mode.control
        self.__command.set_text("")
        self.reset_cursor()

    def execute_command(self):
        self.__mode = Mode.control
        command = self.__command.get_text()
        self.__stdscr.move(0, 0)
        self.__command.set_text("")
        self.reset_cursor()

    def reset_cursor(self):
        self.__stdscr.move(0, 0)

    def update_command(self, ch: int):
        self.__command.handle_input(ch)

    # public API
    def create_collection(self, name: str, activate: bool = False) -> Collection:
        new_collection = Collection(requests=[], name=name)
        self.context.collections.append(new_collection)
        if activate:
            self.set_active_collection(new_collection)
        return new_collection

    def set_active_collection(self, collection: Collection):
        self.__collection_pane.window.move(1, 1)
        length = self.__collection_pane.pane_size[1]
        self.__collection_pane.window.addstr(util.ellipsize(collection.name, length).ljust(length, " "))
        self.__collection.clear()
        for request in collection.requests:
            self.__collection.add_item(request.name)

    def create_request(self):
        pass

