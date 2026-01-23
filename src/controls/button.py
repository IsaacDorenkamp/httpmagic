import curses
import typing

from .control import Control


class Button(Control):
    _text: str
    _shortcut: str | None
    _focus_color: int
    _click: typing.Callable[[], typing.Any] | None

    def __init__(self, text: str, handler: typing.Callable[[], typing.Any] | None = None):
        super().__init__()
        self._text = text
        self._shortcut = None
        self._focus_color = curses.COLOR_GREEN
        self._click = handler

    def on_focus(self):
        self.repaint()

    def handle_input(self, ch: int):
        if ch == Control.RETURN:
            self.unfocus()
            self.repaint()
            if self._click:
                self._click()
        elif ch == Control.ESC:
            self.unfocus()
            self.repaint()

    def render(self):
        self._win.border()
        text = self._text[:self._width].ljust(self._width, " ")
        if self.size[0] < 2 and self.size[1] < 2:
            return
        self._win.move(1, 1)
        self._win.addnstr(text, self._width - 2)

        if self._shortcut is not None:
            index = self._text.index(self._shortcut)
            if index >= 0:
                self._win.move(1, 1 + index)
                self._win.attron(curses.A_UNDERLINE)
                self._win.addch(self._shortcut)
                self._win.attroff(curses.A_UNDERLINE)

    @property
    def shortcut(self) -> str | None:
        return self._shortcut

    @shortcut.setter
    def shortcut(self, value: str | None):
        self._shortcut = value

    @property
    def click(self):
        return self._click

    @click.setter
    def click(self, value):
        self._click = value

    @property
    def _width(self) -> int:
        return self._size[1]

