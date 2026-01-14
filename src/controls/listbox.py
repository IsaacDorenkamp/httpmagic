import bisect
import curses
import typing

import colors
import util

from .control import Control


class ListBox(Control):
    _win: curses.window

    _items: list[str]
    _location: tuple[int, int]
    _size: tuple[int, int]
    _scroll: int
    _selection: int

    def __init__(self, parent: curses.window, location: tuple[int, int], size: tuple[int, int]):
        super().__init__()
        self._create_window(parent, size, location)
        self._items = []
        self._location = location
        self._size = size
        self._selection = -1
        self._scroll = 0

    def clear(self):
        self._items = []
        self._win.erase()
        self._win.refresh()

    def try_focus(self):
        if self._selection == -1 and self._items:
            self._selection = 0
            self.__draw_row(0)

    def on_unfocus(self):
        if self._selection != -1:
            selection = self._selection
            self._selection = -1
            self.__draw_row(selection)

    def handle_input(self, ch: int):
        initial_selection = self._selection
        if ch == curses.KEY_DOWN or ch == ord('j'):
            self._selection = min(len(self._items) - 1, self._selection + 1)
        elif ch == curses.KEY_UP or ch == ord('k'):
            self._selection = max(0, self._selection - 1)

        if self._selection >= 0 and not self._items:
            self._selection = -1

        redrawn = self.__adjust_offset()
        if not redrawn:
            # redraw only relevant rows
            self.__draw_row(initial_selection)
            self.__draw_row(self._selection, True)

    def _update_focused(self):
        if self.focused and self._selection == -1:
            self._selection = 0

    def add_item(self, item: str):
        self._items.append(item)

        self._update_focused()

        # check if new item is in visible range
        if len(self._items) <= self._scroll + self._size[0]:
            self.__draw_row(len(self._items)-1, True)

    def insert_item(self, item: str, at: int):
        self._items.insert(at, item)
        if at <= self._selection:
            self._selection += 1
        self._update_focused()
        if self._scroll <= at <= self._scroll + self._size[0]:
            for row in range(at, self._scroll + self._size[0]):
                self.__draw_row(row)
            self._win.refresh()

    def insort_item(self, item: str, key: typing.Callable[[str], typing.Any] | None = None):
        index = bisect.bisect(self._items, key(item) if key else item, key=key)
        self._items.insert(index, item)
        if index <= self._selection:
            self._selection += 1
        self._update_focused()
        self.repaint()

    def resort(self, key: typing.Callable[[str], typing.Any]):
        self._items.sort(key=key)
        self.repaint()

    def render(self):
        for row in range(self._scroll, self._scroll + self._size[0]):
            self.__draw_row(row)

        if self._selection >= 0:
            self._win.move(self._selection - self._scroll, 0)

    def __draw_row(self, row: int, refresh: bool = False):
        if row > len(self._items) - 1 or row == -1:
            return

        render_row = row - self._scroll
        self._win.move(render_row, 0)
        usecolor = row == self._selection
        attr = colors.color_pair(self.background, self.foreground)
        back_attr = colors.color_pair(self.foreground, self.background)
        self._win.addstr(util.ellipsize(self._items[row], self._size[1]).ljust(self._size[1], " "), attr if usecolor else back_attr)

        self._win.move(render_row, 0)
        if refresh:
            self._win.refresh()

    def __adjust_offset(self) -> bool:
        repaint = True
        if self._selection < self._scroll:
            self._scroll = self._selection
        elif self._selection >= self._scroll + self._size[0]:
            self._scroll = self._selection - self._size[0] + 1
        else:
            repaint = False

        if repaint:
            self.repaint()

        return repaint

