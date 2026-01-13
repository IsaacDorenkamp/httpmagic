import curses

from .control import Control


class LineEdit(Control):
    _win: curses.window

    _width: int
    _location: tuple[int, int]
    _text: str
    _cursor: int
    _offset: int

    def __init__(self, stdscr: curses.window, location: tuple[int, int], width: int):
        super().__init__()
        self._create_window(stdscr, (1, width), location)
        self._width = width
        self._location = location
        self._text = ""
        self._cursor = 0
        self._offset = 0

    def set_text(self, text: str):
        self._text = text
        self._cursor = len(self._text)
        self._offset = max(self._cursor, self._width) - self._width
        self.repaint()

    def get_text(self) -> str:
        return self._text

    def render(self):
        portion = self._text[self._offset:self._offset+self._width]
        self._win.clear()
        try:
            with self.usecolor(self._win):
                self._win.addstr(0, 0, portion)
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
            self._text = self._text[:self._cursor-1] + self._text[self._cursor:]
            self._cursor -= 1
        elif ch == curses.KEY_LEFT:
            self._cursor = max(0, self._cursor - 1)
        elif ch == curses.KEY_RIGHT:
            self._cursor = min(len(self._text), self._cursor+1)
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

