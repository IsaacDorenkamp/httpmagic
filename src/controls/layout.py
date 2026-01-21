from abc import ABCMeta, abstractmethod
import collections
import curses
import typing

from .control import Control


T = typing.TypeVar("T")


class Layout(typing.Generic[T], metaclass=ABCMeta):
    @abstractmethod
    def add_child(self, child: Control, data: T):
        raise NotImplementedError()

    @abstractmethod
    def remove_child(self, child: Control):
        raise NotImplementedError()

    @abstractmethod
    def arrange(self, window: curses.window):
        raise NotImplementedError()


class GridData:
    row: int
    col: int
    row_span: int
    col_span: int

    def __init__(self, row: int, col: int, row_span: int = 1, col_span: int = 1):
        self.row = row
        self.col = col
        self.row_span = row_span
        self.col_span = col_span


class GridLayout(Layout[GridData]):
    _items: dict[Control, GridData]
    padding: tuple[int, int]

    def __init__(self, padding: tuple[int, int] = (0, 0)):
        self._items = {}
        self.padding = padding

    def add_child(self, child: Control, data: GridData):
        if child in self._items:
            raise ValueError("'%s' is already in this layout!" % str(child))
        self._items[child] = data

    def remove_child(self, child: Control):
        del self._items[child]

    def arrange(self, window: curses.window):
        if not self._items:
            return

        size = window.getmaxyx()
        num_rows = max(((grid_data.row + grid_data.row_span - 1) for grid_data in self._items.values())) + 1
        num_cols = max(((grid_data.col + grid_data.col_span - 1) for grid_data in self._items.values())) + 1

        # TODO: determine cell size. by default, try to expand component to cell,
        # but if not possible, attempt refer to GridData (will need to add new fields)
        # to determine how the component should be positioned within the cell.
        cell_size = ((size[0] - (2 * self.padding[0])) // num_rows, (num_cols - (2 * self.padding[1])) // num_cols)

        # TODO: do not just dump remainder at end of container
        for control, grid_data in self._items.items():
            desired_size = cell_size[0] * grid_data.row_span, cell_size[1] * grid_data.col_span
            with control.rearrange():
                expanded = control.set_size(desired_size)
                # TODO: take expanded into consideration
                control.set_pos((cell_size[0] * grid_data.row + self.padding[0], cell_size[1] * grid_data.col + self.padding[1]))

