import curses
import logging

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
        self._win = parent.derwin(*size, *location)
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
        if ch == curses.KEY_DOWN:
            self._selection = min(len(self._items) - 1, self._selection + 1)
        elif ch == curses.KEY_UP:
            self._selection = max(0, self._selection - 1)

        redrawn = self.__adjust_offset()
        if not redrawn:
            # redraw only relevant rows
            self.__draw_row(initial_selection)
            self.__draw_row(self._selection)

    def add_item(self, item: str):
        self._items.append(item)

        # check if new item is in visible range
        if len(self._items) <= self._scroll + self._size[0]:
            self.__draw_row(len(self._items)-1)

    def __redraw(self):
        self._win.erase()
        for row in range(self._scroll, self._scroll + self._size[0]):
            self.__draw_row(row)

        self._win.move(self._selection - self._scroll, 0)
        self._win.refresh()

    def __draw_row(self, row: int):
        render_row = row - self._scroll
        self._win.move(render_row, 0)
        usecolor = row == self._selection
        attr = colors.color_pair(curses.COLOR_BLACK, curses.COLOR_WHITE)
        if usecolor: self._win.attron(attr)
        try:
            self._win.addstr(util.ellipsize(self._items[row], self._size[1]).ljust(self._size[1], " "))
        except curses.error:
            # note: this can occur when the bottom-right cell is written to.
            # thus, we shall ignore errors of this type.
            pass
        if usecolor: self._win.attroff(attr)

        self._win.move(render_row, 0)
        self._win.refresh()

    def __adjust_offset(self) -> bool:
        redraw = True
        if self._selection < self._scroll:
            self._scroll = self._selection
        elif self._selection >= self._scroll + self._size[0]:
            self._scroll = self._selection - self._size[0] + 1
        else:
            redraw = False

        if redraw:
            self.__redraw()

        return redraw

