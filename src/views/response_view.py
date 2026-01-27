from __future__ import annotations
import io
import typing

import colors
from controls import Panel, SwitchPane, TabBar
from controls.layout import LineFlexData, LineFlexLayout
from entities.response import Response

from .response.text import TextResponseView
from .response.binary import BinaryResponseView

if typing.TYPE_CHECKING:
    from ..app import App


def take_lines(text: str, max_line_length: int, max_lines: int):
    line = io.StringIO()
    line_length = 0
    lines_produced = 0
    for ch in text:
        if ch == '\n' or line_length == max_line_length:
            yield line.getvalue()
            line = io.StringIO()
            line_length = 0
            lines_produced += 1
            if lines_produced == max_lines:
                return
            continue

        line.write(ch)
        line_length += 1

    if line_length > 0:
        yield line.getvalue()


class ResponseView(Panel):
    __response: Response | None
    __loading: bool

    __view: SwitchPane
    __text_view: TextResponseView

    def __init__(self, abs_pos: tuple[int, int], size: tuple[int, int], parent: App):
        super().__init__(abs_pos=abs_pos, size=size, parent=parent.stdscr)
        self.__response = None
        self.__loading = False

        self.__tabs = TabBar(parent=self._win)
        self.__tabs.foreground = colors.get_color("background")
        self.__tabs.background = colors.get_color("foreground")

        self.__view = SwitchPane(parent=self._win)
        self.__text_view = TextResponseView(parent=self.__view._win)
        self.__binary_view = BinaryResponseView(parent=self.__view._win)

        self.add(self.__view)
        self.add(self.__tabs)
        self.__view.add(self.__text_view)

        self.__tabs.set_relative_pos((0, 1))
        self.__tabs.set_size((1, self._size[1] - 2))
        self.__tabs.add_tab("Text", select=True)
        self.__tabs.add_tab("Binary")
        self.__tabs.change = self.__switch_tab

        layout = LineFlexLayout()
        layout.add_child(self.__view, LineFlexData(line=0, order=0, stretch=True))
        layout.set_line_weight(0, 1)
        self.set_layout(layout)

        self.__view.set_active(self.__text_view)

    def render(self):
        super().render()
        if self.__loading:
            self._win.move(1 + self.padding[0], 1 + self.padding[1])
            self._win.addnstr("Loading...", self.content_size[1])
            self._win.refresh()
            return

    def set_loading(self, loading: bool):
        if self.__loading != loading:
            self.__loading = loading
            if loading:
                self.__view.set_active(None)
            else:
                self.__view.set_active(self.__text_view)
            self.repaint()

    def set_response(self, response: Response | None, reset_loading: bool = True):
        if self.__response == response:
            return

        self.__loading = False if reset_loading else self.__loading
        self.__response = response
        if response is not None:
            self.__text_view.set_content(response.data)
        else:
            self.__text_view.set_content(b"")
        self.repaint()

    def __switch_tab(self, tab: str | None):
        active = None
        if tab == "Text":
            active = self.__text_view
        elif tab == "Binary":
            active = self.__binary_view

        self.__view.set_active(active)

    @property
    def tabs(self) -> TabBar:
        return self.__tabs

