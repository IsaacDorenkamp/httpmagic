from __future__ import annotations
import curses
import logging
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

    def __init__(self, parent: App, pos: tuple[int, int], size: tuple[int, int]):
        super().__init__(parent.stdscr, pos, size)

        self.__app = parent
        self.__method = OptionBox(self._win, (3, 15), 7)
        self.__url = LineEdit(self._win, (3, 28), size[1] - 35)
        self.__url.background = colors.parse_color(parent.context.settings.colors.contrast)
        self.__url.change = self.update_url

        self.__send = Button(self._win, (size[0] - 4, size[1] - 16), 15, "Send")
        self.__send.shortcut = 'S'
        self.__send.click = parent.execute_request

        for method in Method:
            self.__method.add_option(method.value, colors.color_pair(method.color, self.background))

        self.__method.set_option("GET")

    def handle_input(self, ch: int):
        if ch == ord('m'):
            self.__app.set_focus(self.__method)
        elif ch == ord('u'):
            self.__app.set_focus(self.__url)
        elif ch == ord('S'):
            self.__app.set_focus(self.__send)

    def update_url(self, url):
        valid = True
        try:
            data = urlparse(url)
            if data.scheme not in ["http", "https"]:
                valid = False
        except ValueError:
            valid = False

        self.__url.background = curses.COLOR_RED if not valid else colors.parse_color(self.__app.context.settings.colors.contrast)

    def render(self):
        super().render()

        # label
        self._win.move(3, 7)
        self._win.attron(curses.A_UNDERLINE)
        self._win.addch("M")
        self._win.attroff(curses.A_UNDERLINE)
        self._win.addstr("ethod:")
        self.__method.render()

        self._win.move(3, 23)
        self._win.attron(curses.A_UNDERLINE)
        self._win.addch("U")
        self._win.attroff(curses.A_UNDERLINE)
        self._win.addstr("RL:")
        self.__url.render()

        self.__send.render()

        self._win.refresh()

