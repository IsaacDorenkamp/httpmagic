from __future__ import annotations
import io
import logging
import typing

from controls import Panel
from entities.response import Response

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

    def __init__(self, parent: App, pos: tuple[int, int], size: tuple[int, int]):
        super().__init__(parent.stdscr, pos, size)
        self.__response = None
        self.__loading = False

    def render(self):
        super().render()

        if self.__loading:
            self._win.move(1, 1)
            self._win.addnstr("Loading...", self.pane_size[1] - 2)
            return

        if self.__response is None:
            return

        try:
            data = self.__response.data.decode('utf-8')
        except:
            logging.exception("failed")
            self._win.addnstr("[binary data]", self.pane_size[1] - 2)
            return

        line_no = 1
        for line in take_lines(data, self.pane_size[1], self.pane_size[0]):
            self._win.move(line_no, 1)
            self._win.addnstr(line, self.pane_size[1])
            line_no += 1
            

    def set_loading(self, loading: bool):
        if self.__loading != loading:
            self.__loading = loading
            self.repaint()

    def set_response(self, response: Response, reset_loading: bool = True):
        if self.__response == response:
            return

        self.__loading = False if reset_loading else self.__loading
        self.__response = response
        self.repaint()

