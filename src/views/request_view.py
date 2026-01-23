from __future__ import annotations
import curses
from urllib.parse import urlparse
import typing

import colors
from controls import Button, OptionBox, Label, LineEdit, Panel
from controls.layout import GridData, GridLayout
from entities.request import Method

if typing.TYPE_CHECKING:
    from ..app import App


class RequestView(Panel):
    __app: App

    __layout: GridLayout

    __method: OptionBox
    __url: LineEdit
    __send: Button

    def __init__(self, parent: App, pos: tuple[int, int], size: tuple[int, int]):
        super().__init__(parent.stdscr, pos, size)

        self.__layout = GridLayout()

        self.__app = parent
        self.__method_lbl = Label(self._win, (0, 0), (1, 1), "Method: ")
        self.__method = OptionBox(self._win, (3, 15), 7)
        self.__method.change = self.update_method
        self.__url_lbl = Label(self._win, (0, 0), (1, 1), "URL: ")
        self.__url = LineEdit(self._win, (3, 28), size[1] - 35)
        self.__url.background = colors.get_color("contrast")
        self.__url.change = self.update_url

        #self.__send = Button(self._win, (size[0] - 4, size[1] - 16), 15, "Send")
        #self.__send.shortcut = 'S'
        #self.__send.click = parent.execute_request

        for method in Method:
            self.__method.add_option(method.value, colors.color_pair(method.color, self.background))

        self.__method.set_option("GET")

        with self.no_repaint():
            self.add_child(self.__url_lbl)
            self.add_child(self.__url)
            #self.add_child(self.__send)
            self.add_child(self.__method_lbl)
            self.add_child(self.__method)

        self.__layout.padding = (2, 4)
        self.__layout.add_child(self.__method_lbl, GridData(row=0, col=0))
        self.__layout.add_child(self.__method, GridData(row=0, col=1))
        self.__layout.add_child(self.__url_lbl, GridData(row=0, col=2))
        self.__layout.add_child(self.__url, GridData(row=0, col=3, col_span=6))
        self.set_layout(self.__layout)

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

