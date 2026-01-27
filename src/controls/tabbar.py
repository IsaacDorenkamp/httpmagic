import curses
import typing

import colors
from .control import Control


class TabBar(Control):
    __tabs: list[str]
    __selection: int
    __orig_bg: int
    __orig: int

    change: typing.Callable[[str | None], typing.Any] | None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__tabs = []
        self.__selection = -1
        self.__orig_bg = self.background
        self.__orig = -1
        self.change = None

    def on_focus(self):
        self.__orig = self.__selection
        self.__orig_bg = self.background
        self.background = colors.get_color("contrast")
        self.repaint()

    def on_unfocus(self):
        self.background = self.__orig_bg
        self.repaint()

    def render(self):
        row = 0
        self._win.move(row, 0)
        remaining_rows = self._size[0]
        remaining_columns = self._size[1]
        import logging
        for index, tab in enumerate(self.__tabs):
            padded = f" {tab} "
            if len(padded) < remaining_columns:
                logging.debug(f"is selected? {self.__selection == index}")
                self._win.addstr(padded, ((curses.A_BOLD | curses.A_ITALIC) if self.__selection == index else 0))
                remaining_columns -= len(padded)
            else:
                remaining_rows -= 1
                if remaining_rows > 0:
                    row += 1
                    self._win.move(row, 0)
                else:
                    break

            if remaining_columns > 0:
                self._win.addch('\u2502')
                remaining_columns -= 1

        logging.debug("")

    def handle_input(self, ch: int):
        repaint = False
        if ch == ord('h'):
            if self.__selection == -1:
                self.__selection = len(self.__tabs) - 1
            else:
                self.__selection = len(self.__tabs) - 1 if self.__selection == 0 else self.__selection - 1
            repaint = True
        elif ch == ord('l'):
            if self.__selection == -1:
                self.__selection = 0
            else:
                self.__selection = (self.__selection + 1) % len(self.__tabs)
            repaint = True
        elif ch == ord('\n'):
            self.unfocus()
        elif ch == Control.ESC:
            self.__selection = self.__orig
            self.unfocus()

        if repaint:
            self.repaint()

    def add_tab(self, tab: str, select: bool = False):
        self.__tabs.append(tab)
        if select:
            self.set_selection(len(self.__tabs) - 1)
        else:
            self.repaint()

    def set_selection(self, selection: int, fire: bool = True):
        if selection < -1 or selection >= len(self.__tabs):
            raise ValueError("Invalid tab index: %d" % selection)
        self.__selection = selection

        if fire and self.change is not None:
            self.change(None if self.__selection == -1 else self.__tabs[self.__selection])

        self.repaint()

