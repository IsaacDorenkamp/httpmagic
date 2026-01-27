import curses

from controls import Control


class TextResponseView(Control):
    _content: str
    _lines: list[str]
    _offset: tuple[int, int]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._content = ""
        self._offset = 0, 0
        self._lines = []

    def set_content(self, content: bytes):
        try:
            self._content = content.decode('utf-8')
        except UnicodeDecodeError:
            self._content = "[binary data]"
        self.__produce_lines()
        self.__adjust_offset()
        self.repaint()

    def render(self):
        self._win.scrollok(False)
        for line_no, line in enumerate(self._lines[self._offset[0]:self._offset[0]+self._size[0]]):
            self._win.move(line_no, 0)
            try:
                self._win.addnstr(line[self._offset[1]:], self._size[1])
            except curses.error:
                pass
        self._win.scrollok(True)

    def handle_input(self, ch: int):
        pass

    def __produce_lines(self):
        self._lines = self._content.split("\n")

    def __adjust_offset(self):
        if self._offset[0] + self._size[0] > len(self._lines):
            offset_y = max(0, len(self._lines) - self._size[0])
        else:
            offset_y = self._offset[0]

        longest_line = max(len(line) for line in self._lines[self._offset[0]:self._offset[0]+self._size[0]] or [""])
        if self._offset[1] + self._size[1] > longest_line:
            offset_x = max(0, longest_line - self._size[1])
        else:
            offset_x = self._offset[1]

        self._offset = offset_y, offset_x

