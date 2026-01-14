import curses

from .control import Control


class OptionBox(Control):
    __options: list[tuple[str, int]]
    __candidate: str | None
    __selection: tuple[str, int] | None
    __pos: tuple[int, int]
    __width: int

    def __init__(self, parent: curses.window, pos: tuple[int, int], width: int):
        super().__init__()
        self._create_window(parent, (1, width), pos)
        self.__options = []
        self.__candidate = None
        self.__selection = None
        self.__pos = pos
        self.__width = width

    def try_focus(self):
        curses.curs_set(2)
        self.__selection = None
        self.__candidate = None
        self.repaint()

    def on_unfocus(self):
        curses.curs_set(0)

    def render(self):
        self._win.move(0, 0)
        try:
            if self.__selection is not None:
                self._win.addnstr(self.__selection[0], self.__width, self.__selection[1])
            elif self.__candidate is not None:
                self._win.addnstr(self.__candidate, self.__width)
        except curses.error:
            pass

    def add_option(self, option: str, attributes: int = 0):
        self.__options.append((option, attributes))

    def set_option(self, option: str):
        for candidate in self.__options:
            if candidate[0] == option:
                self.__selection = candidate
                self.__candidate = None
                self.repaint()
                return

        raise ValueError("no option '%s'" % option)

    def handle_input(self, ch: int):
        if 32 <= ch < 127:
            new_str = (self.__candidate or "") + chr(ch)
            # find all matching candidates
            matches = [option for option in self.__options if option[0].startswith(new_str)]
            if not matches:
                # TODO: indicate some issue
                pass
            elif len(matches) == 1:
                # Found a single match!
                self.__selection = matches[0]
                self.__candidate = None
                self.repaint()
                self.unfocus()
            else:
                self.__candidate = new_str
                self.repaint()
        elif ch == 27:
            self.unfocus()

