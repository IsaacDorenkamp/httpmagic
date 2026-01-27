import curses
import io

from .control import Control


class Label(Control):
    _text: str
    _lines: list[str]

    _bold: int
    _italic: int
    _underline: int
    _fill: bool

    def __init__(self, text: str = "", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._win.scrollok(False)
        self._text = text
        self._bold = False
        self._italic = False
        self._underline = False
        self._fill = False
        self.__produce_lines()

    def handle_input(self, ch: int):
        pass

    def get_text(self) -> str:
        return self._text

    def set_text(self, text: str):
        self._text = text
        self.__produce_lines()
        self.repaint()

    @property
    def bold(self) -> bool:
        return self._bold == curses.A_BOLD

    @bold.setter
    def bold(self, value: bool):
        self._bold = curses.A_BOLD if value else 0
        self.repaint()

    @property
    def italic(self) -> bool:
        return self._italic == curses.A_ITALIC

    @italic.setter
    def italic(self, value: bool):
        self._italic = curses.A_ITALIC if value else 0
        self.repaint()

    @property
    def underline(self) -> bool:
        return self._underline == curses.A_UNDERLINE

    @underline.setter
    def underline(self, value: bool):
        self._underline = curses.A_UNDERLINE if value else 0
        self.repaint()

    @property
    def fill(self) -> bool:
        return self._fill

    @fill.setter
    def fill(self, value: bool):
        self._fill = value
        self.repaint()

    def render(self):
        if not self._lines:
            self._win.move(0, 0)
            try:
                self._win.addnstr(" " * self._size[1], self._size[1])
            except curses.error:
                pass
            return

        for index, line in enumerate(self._lines):
            self._win.move(index, 0)
            try:
                self._win.addnstr(line.ljust(self._size[1], " ") if self.fill else line, self._size[1], self._bold | self._italic | self._underline)
            except curses.error:
                pass

    def set_size(self, size: tuple[int, int]):
        result = super().set_size(size)
        self.__produce_lines()
        return result

    def __produce_lines(self):
        line = io.StringIO()
        lines = []
        n_length = 0
        n_lines = 0
        for ch in self._text:
            if ch == '\n':
                lines.append(line.getvalue())
                line = io.StringIO()
                n_lines += 1
                n_length = 0
            else:
                line.write(ch)
                n_length += 1
                if n_length >= self._size[1]:
                    lines.append(line.getvalue())
                    line = io.StringIO()
                    n_lines += 1
                    n_length = 0

            if n_lines >= self._size[0]:
                break

        remainder = line.getvalue()
        if remainder:
            lines.append(remainder)

        self._lines = lines[:self._size[0]]

