import curses
import typing

from .control import Control


class LineEdit(Control):
    _text: str
    _cursor: int
    _offset: int
    _change: typing.Callable[[str], typing.Any] | None
    _buffer: str

    def __init__(self, width: int, *args, **kwargs):
        super().__init__(size=(1, width), focus_greedy=True, *args, **kwargs)
        self._text = ""
        self._buffer = ""
        self._cursor = 0
        self._offset = 0
        self._change = None
        self.max_size = 1, None

    def on_focus(self):
        self._buffer = self._text
        self._win.move(0, self._cursor - self._offset)
        self._win.refresh()
        curses.curs_set(2)

    def on_unfocus(self):
        curses.curs_set(0)

    def set_text(self, text: str):
        self._text = text
        self._cursor = len(self._text)
        self._offset = max(self._cursor, self._width) - self._width
        self.repaint()

    def get_text(self) -> str:
        return self._text

    def render(self):
        portion = self._text[self._offset:self._offset+self._width].ljust(self._width, " ")
        try:
            self._win.addnstr(0, 0, portion, self._width)
        except curses.error:
            pass

        if self.focused:
            self._win.move(0, self._cursor - self._offset)

    def handle_input(self, ch: int):
        redraw = True
        if 32 <= ch < 127:
            # append character at cursor
            self._text = self._text[:self._cursor] + chr(ch) + self._text[self._cursor:]
            self._cursor += 1
        elif ch == curses.KEY_BACKSPACE or ch == 127:
            if self._cursor == 0:
                return
            self._text = self._text[:self._cursor-1] + self._text[self._cursor:]
            self._cursor -= 1
        elif ch == curses.KEY_LEFT:
            self._cursor = max(0, self._cursor - 1)
        elif ch == curses.KEY_RIGHT:
            self._cursor = min(len(self._text), self._cursor+1)
        elif ch in [Control.RETURN, Control.ESC]:
            if ch == Control.ESC:
                self.set_text(self._buffer)
            elif self.change:
                self.change(self._text)
            self.unfocus()
        elif ch == Control.CTRL_B:
            self._cursor = 0
        elif ch == Control.CTRL_C:
            self._cursor = len(self._text)
        elif ch == Control.CTRL_E:
            self._text = ""
            self._cursor = 0
            self._offset = 0
        else:
            redraw = False

        if redraw:
            self.__pull_offset()
            self.repaint()

    def __pull_offset(self):
        if self._cursor == len(self._text):
            self._offset = max(self._cursor, self._width - 1) - self._width + 1
        elif self._cursor - self._offset > self._width - 1:
            self._offset = self._cursor - self._width + 1
        elif self._cursor < self._offset:
            self._offset = self._cursor

    @property
    def change(self):
        return self._change

    @change.setter
    def change(self, value):
        self._change = value

    @property
    def _width(self) -> int:
        return self._size[1]

    def set_size(self, size: tuple[int, int]) -> bool:
        result = super().set_size(size)
        self.__pull_offset()
        self.repaint()
        return result

