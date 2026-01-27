import curses
import typing

import colors
from .control import Control


class Button(Control):
    _text: str
    _shortcut: str | None
    _focus_color: int
    _click: typing.Callable[[], typing.Any] | None

    def __init__(self, text: str, handler: typing.Callable[[], typing.Any] | None = None, parent: curses.window | None = None):
        super().__init__(parent=parent)
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
        small = self._size[0] < 3
        focus_color_pair = colors.color_pair(self._focus_color, self.background)
        if not small:
            if self.focused: self._win.attron(focus_color_pair)
            self._win.border()
            if self.focused: self._win.attroff(focus_color_pair)
        text = self._text[:self._width]

        start = 0 if small else 1
        self._win.move(start, start)
        focus_attr = focus_color_pair if self.focused else 0
        text_width = self._width if small else self._width - 2
        prepad = " " * (max(0, text_width - len(text)) // 2)
        try:
            self._win.addnstr(prepad + text, self._width if small else self._width - 2, focus_attr | curses.A_UNDERLINE if small else 0)
        except curses.error:
            pass

        if self._shortcut is not None:
            index = self._text.index(self._shortcut)
            if index >= 0:
                self._win.move(start, start + index + len(prepad))
                attr = (curses.A_UNDERLINE if small else 0) | (focus_attr if small else 0)
                try:
                    self._win.addch(self._shortcut, attr)
                except curses.error:
                    pass

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

