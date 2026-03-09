from __future__ import annotations
from urllib.parse import urlparse
import typing

import framed
from framed.widgets import *
from entities.request import Method

if typing.TYPE_CHECKING:
    from ..app import App


class RequestView(framed.Panel):
    method_label: Label
    method: OptionBox
    url_label: Label
    url: Editor

    def __init__(self, region: framed.rect2, owner: framed.Manager):
        super().__init__(region, owner)
        self.method_label = Label("Method:")
        self.method = OptionBox()
        self.url_label = Label("URL:")
        self.url = Editor(model_cls=LineTextModel)

        self.add(self.method_label)
        self.add(self.method)
        self.add(self.url_label)
        self.add(self.url)

    def arrange(self):
        flex = self.flex()
        flex.add(self.method_label, row=0, weight=1)
        flex.add(self.method, row=0, weight=1)
        flex.add(self.url_label, row=0, weight=1)
        flex.add(self.url, row=0, weight=3)


"""
class _RequestView(TitledPanel):
    __app: App

    __method: OptionBox
    __url: LineEdit
    __send: Button

    __dirty: bool
    __request_name: str

    def __init__(self, abs_pos: tuple[int, int], size: tuple[int, int], parent: App):
        super().__init__(title="", abs_pos=abs_pos, size=size, parent=parent.stdscr)

        self.__dirty = False
        self.__request_name = ""

        self.padding = 1, 2

        self.__app = parent
        self.__method_lbl = Label("Method: ", parent=self._win)
        self.__method = OptionBox(parent=self._win)
        self.__method.change = self.update_method
        self.__url_lbl = Label("URL: ", parent=self._win)
        self.__url = LineEdit(10, parent=self._win)
        self.__url.background = colors.get_color("contrast")
        self.__url.change = self.update_url

        self.__send = Button("Send", parent=self._win)
        self.__send.shortcut = 'S'
        self.__send.click = parent.execute_request

        for method in Method:
            self.__method.add_option(method.value, colors.color_pair(method.color, self.background))

        self.__method.set_option("GET")

        self.add(self.__url_lbl)
        self.add(self.__url)
        self.add(self.__send)
        self.add(self.__method_lbl)
        self.add(self.__method)

        self.__layout = LineFlexLayout()
        self.__layout.add_child(self.__method_lbl, LineFlexData(line=0, order=0, min_width=8))
        self.__layout.add_child(self.__method, LineFlexData(line=0, order=1, min_width=8))
        self.__layout.add_child(self.__url_lbl, LineFlexData(line=0, order=2, min_width=5))
        self.__layout.add_child(self.__url, LineFlexData(line=0, order=3, stretch=True, min_width=1))
        self.__layout.add_spacer(LineFlexData(line=2, order=0, stretch=True))
        self.__layout.add_child(self.__send, LineFlexData(line=2, order=1, stretch=False, min_width=10))
        self.__layout.set_line_weight(1, 1)
        self.__layout.set_line_min_height(2, 3)
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
        if self.__app.context.active_request and propagate:
            request = self.__app.context.active_request
            request.url = url
            self.__app.context.dirty.add(request.id)
            self.set_dirty(True)

    def update_method(self, method: str):
        if self.__app.context.active_request:
            request = self.__app.context.active_request
            request.method = Method(method)
            self.__app.context.dirty.add(request.id)
            self.set_dirty(True)

    def set_request_name(self, request_name: str, dirty: bool | None = None):
        self.__request_name = request_name
        if dirty is not None:
            self.set_dirty(dirty)
        else:
            self.__update_title()

    def set_dirty(self, dirty: bool):
        self.__dirty = dirty
        self.__update_title()

    def __update_title(self):
        self.set_title(f"{'* ' if self.__dirty else ''}{self.__request_name}")
"""
