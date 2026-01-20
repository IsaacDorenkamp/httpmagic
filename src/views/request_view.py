from __future__ import annotations
import curses
from urllib.parse import urlparse
import typing

import colors
from controls import Button, OptionBox, LineEdit, Panel
from entities.request import Method

if typing.TYPE_CHECKING:
    from ..app import App


class RequestView(Panel):
    __app: App

    __method: OptionBox
    __url: LineEdit
    __send: Button

    def __init__(self, parent: App, pos: tuple[int, int], size: tuple[int, int]):
        super().__init__(parent.stdscr, pos, size)

        self.__app = parent
        self.__method = OptionBox(self._win, (3, 15), 7)
        self.__method.change = self.update_method
        self.__url = LineEdit(self._win, (3, 28), size[1] - 35)
        self.__url.background = colors.get_color("contrast")
        self.__url.change = self.update_url

        self.__send = Button(self._win, (size[0] - 4, size[1] - 16), 15, "Send")
        self.__send.shortcut = 'S'
        self.__send.click = parent.execute_request

        for method in Method:
            self.__method.add_option(method.value, colors.color_pair(method.color, self.background))

        self.__method.set_option("GET")

        with self.no_repaint():
            self.add_child(self.__url)
            self.add_child(self.__send)
            self.add_child(self.__method)

    def set_method(self, method: Method):
        self.__method.set_option(method)

    def set_url(self, url: str):
        self.__url.set_text(url)
        self.update_url(url, propagate=False)

    def handle_input(self, ch: int):
        if self.visible:
            if ch == ord('m'):
                self.__app.set_focus(self.__method)
            elif ch == ord('u'):
                self.__app.set_focus(self.__url)
            elif ch == ord('S'):
                self.__app.set_focus(self.__send)

    def update_url(self, url, propagate: bool = True):
        valid = True
        try:
            data = urlparse(url)
            if data.scheme not in ["http", "https"]:
                valid = False
        except ValueError:
            valid = False

        self.__url.background = curses.COLOR_RED if not valid else colors.get_color("contrast")
        if valid and self.__app.context.active_request and propagate:
            self.__app.context.active_request.url = url

    def update_method(self, method: str):
        if self.__app.context.active_request:
            self.__app.context.active_request.method = Method(method)

    def render(self):
        super().render()

        if self.content_visible:
            # render labels for controls
            self._win.move(3, 7)
            self._win.attron(curses.A_UNDERLINE)
            self._win.addch("M")
            self._win.attroff(curses.A_UNDERLINE)
            self._win.addstr("ethod:")

            self._win.move(3, 23)
            self._win.attron(curses.A_UNDERLINE)
            self._win.addch("U")
            self._win.attroff(curses.A_UNDERLINE)
            self._win.addstr("RL:")
        else:
            # render an alternative placeholder
            text = "No request selected."
            pos = (self._size[0] // 2, self._size[1] // 2 - len(text) // 2)
            self._win.move(*pos)
            self._win.addstr(text, curses.A_ITALIC)

    def set_visible(self, visible: bool):
        super().set_visible(visible)
        self.__method.set_visible(visible)
        self.__url.set_visible(visible)
        self.__send.set_visible(visible)

