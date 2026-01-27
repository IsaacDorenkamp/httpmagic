import bisect
import curses
import typing

import colors
import util

from .control import Control


class ListBox(Control):
    _items: list[str]
    _scroll: int
    _selection: int
    _prev_selection: int
    _change: typing.Callable[[str | None], typing.Any] | None

    def __init__(self, parent: curses.window | None = None):
        super().__init__(parent=parent)
        self._items = []
        self._selection = -1
        self._prev_selection = -1
        self._scroll = 0
        self._change = None

    def clear(self):
        self._items = []
        self._win.erase()
        self._win.refresh()

    def try_focus(self):
        self._prev_selection = self._selection
        if self._selection == -1 and self._items:
            self._selection = 0
            self.__draw_row(0, refresh=True)

    def on_focus(self):
        self.repaint()

    def on_unfocus(self):
        self._prev_selection = self._selection
        self.repaint()

    def handle_input(self, ch: int):
        initial_selection = self._selection
        if ch == curses.KEY_DOWN or ch == ord('j'):
            self._selection = min(len(self._items) - 1, self._selection + 1)
        elif ch == curses.KEY_UP or ch == ord('k'):
            self._selection = max(0, self._selection - 1)
        elif ch == Control.RETURN:
            self.unfocus()
            if self.change:
                self.change(self._items[self._selection] if self._selection >= 0 else None)
        elif ch == Control.ESC:
            self._selection = self._prev_selection
            self.unfocus()

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

    def insort_item(self, item: str, key: typing.Callable[[str], typing.Any] | None = None, select: bool = False):
        index = bisect.bisect(self._items, key(item) if key else item, key=key)
        self._items.insert(index, item)
        if select:
            self._selection = index
        elif index <= self._selection:
            self._selection += 1
        self._update_focused()
        self.repaint()

    def resort(self, key: typing.Callable[[str], typing.Any]):
        self._items.sort(key=key)
        self.repaint()

    def find(self, item: str) -> int:
        return self._items.index(item)

    def set_item(self, index: int, item: str, resort: typing.Callable[[str], typing.Any] | None = None):
        self._items[index] = item
        if resort is not None:
            self.resort(resort)

    def render(self):
        for row in range(self._scroll, self._scroll + self._size[0]):
            self.__draw_row(row)

    def set_selection(self, index: int):
        if index == -1:
            to_rerender = self._selection
            self._selection = index
            if to_rerender >= 0:
                actual_row = to_rerender - self._scroll
                self.__draw_row(actual_row, refresh=True)
        if index < 0 or index >= len(self._items):
            raise ValueError("selection must be in the range [0, %d)" % len(self._items))

        previous = self._selection
        self._selection = index

        if previous != -1:
            prev_row = previous - self._scroll
            self.__draw_row(prev_row)

        repainted = self.__adjust_offset()
        if not repainted:
            actual_row = self._selection - self._scroll
            self.__draw_row(actual_row, refresh=True)

    def __draw_row(self, row: int, refresh: bool = False):
        back_attr = colors.color_pair(self.foreground, self.background)
        if row > len(self._items) - 1 or row == -1:
            try:
                self._win.addnstr(" " * self._size[1], self._size[1], back_attr)
            except curses.error:
                pass
            return

        render_row = row - self._scroll
        self._win.move(render_row, 0)
        usecolor = row == self._selection
        attr = colors.color_pair(self.background, self.foreground if self.focused else colors.get_color("contrast"))
        try:
            self._win.addnstr(util.ellipsize(self._items[row], self._size[1]).ljust(self._size[1], " "),  self._size[1], attr if usecolor else back_attr)
        except curses.error:
            pass

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

    @property
    def change(self) -> typing.Callable[[str | None], typing.Any] | None:
        return self._change

    @change.setter
    def change(self, value: typing.Callable[[str | None], typing.Any] | None):
        self._change = value

