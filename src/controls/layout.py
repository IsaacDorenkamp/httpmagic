from __future__ import annotations
from abc import ABCMeta, abstractmethod
import bisect
import logging
import typing

from .control import shift_region, Control, ScreenRegion


T = typing.TypeVar("T")


class Layout(typing.Generic[T], metaclass=ABCMeta):
    @abstractmethod
    def add_child(self, child: Control, data: T):
        raise NotImplementedError()

    @abstractmethod
    def remove_child(self, child: Control):
        raise NotImplementedError()

    @abstractmethod
    def arrange(self, abs_region: ScreenRegion):
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

    def arrange(self, abs_region: ScreenRegion) -> bool:
        """
        Arrange the controls managed by this layout in the specified curses window. If anything goes wrong,
        such as if the calculated cell size has either a height or width of 0, then this will return False.
        Otherwise, True is returned.
        """

        if not self._items:
            return True

        size = abs_region.bottom - abs_region.top + 1, abs_region.right - abs_region.left + 1
        num_rows = max(((grid_data.row + grid_data.row_span - 1) for grid_data in self._items.values())) + 1
        num_cols = max(((grid_data.col + grid_data.col_span - 1) for grid_data in self._items.values())) + 1

        # TODO: determine cell size. by default, try to expand component to cell,
        # but if not possible, attempt refer to GridData (will need to add new fields)
        # to determine how the component should be positioned within the cell.
        cell_size = ((size[0] - (2 * self.padding[0])) // num_rows, (size[1] - (2 * self.padding[1])) // num_cols)
        if 0 in [max(0, x) for x in cell_size]:
            return False

        # TODO: do not just dump remainder at end of container
        for control, grid_data in self._items.items():
            desired_size = cell_size[0] * grid_data.row_span, cell_size[1] * grid_data.col_span
            with control.rearrange():
                expanded = control.set_size(desired_size)
                # TODO: take expanded into consideration
                pos = (cell_size[0] * grid_data.row + self.padding[0], cell_size[1] * grid_data.col + self.padding[1])
                control.set_relative_pos(pos)

        return True


class LineFlexData:
    line: int
    order: int
    stretch: bool
    min_width: int

    def __init__(self, line: int, order: int, stretch: bool = False, min_width: int = 1):
        self.line = line
        self.order = order
        self.stretch = stretch
        self.min_width = min_width


class LineFlexLayout(Layout[LineFlexData]):
    __items: dict[Control, LineFlexData]
    __line_weights: dict[int, int]
    __line_min_height: dict[int, int]
    __positions: list[tuple[ScreenRegion, Control]]

    def __init__(self):
        self.__items = {}
        self.__line_weights = {}
        self.__line_min_height = {}
        self.__positions = []

    def add_child(self, child: Control, data: LineFlexData):
        self.__items[child] = data
        self.__positions.clear()

    def remove_child(self, child: Control):
        del self.__items[child]
        self.__positions.clear()

    def set_line_weight(self, line: int, weight: int):
        self.__line_weights[line] = weight
        self.__positions.clear()

    def set_line_min_height(self, line: int, min_height: int):
        self.__line_min_height[line] = min_height

    def arrange(self, abs_region: ScreenRegion):
        self.__recompute(abs_region)
        for local_region, control in self.__positions:
            control_abs_region = shift_region(local_region, (abs_region.top, abs_region.left))
            with control.rearrange():
                control.set_absolute_pos((control_abs_region.top, control_abs_region.left))
                control.set_size((control_abs_region.bottom - control_abs_region.top + 1, control_abs_region.right - control_abs_region.left + 1))

    def __recompute(self, abs_region: ScreenRegion):
        total_lines = max(line_data.line for line_data in self.__items.values()) + 1
        by_line: list[list[tuple[Control, LineFlexData]]] = [[] for _ in range(total_lines)]
        for control, data in self.__items.items():
            bisect.insort(by_line[data.line], (control, data), key=lambda data: data[1].order)

        total_weights = sum(weight for weight in self.__line_weights.values())
        total_zero_lines = sum(self.__line_min_height.get(line_no, 1) if self.__line_weights.get(line_no, 0) == 0 else 0 for line_no in range(total_lines))

        rows, columns = abs_region.bottom - abs_region.top + 1, abs_region.right - abs_region.left + 1

        num_weighted_rows = max(0, rows - total_zero_lines)
        weight_unit = max(1, num_weighted_rows // max(1, total_weights))

        available_rows = rows
        current_row = 0
        for line_no, line in enumerate(by_line):
            weight = self.__line_weights.get(line_no, 0)
            want_rows = max(self.__line_min_height.get(line_no, 1), 1 if weight == 0 else weight * weight_unit)
            row_height = min(available_rows, want_rows)
            available_rows -= row_height

            # now calculating column distribution
            control_widths = []
            available_columns = columns
            for control, data in line:
                want_columns = data.min_width
                column_width = min(available_columns, want_columns)
                control_widths.append(column_width)
                available_columns -= column_width

            has_stretch = any(data.stretch for _, data in line)
            while available_columns > 0 and has_stretch:
                for index, entry in enumerate(line):
                    control, data = entry
                    if data.stretch:
                        control_widths[index] += 1
                        available_columns -= 1

                    if available_columns == 0:
                        break

            column_pos = 0
            for column_no, column_width in enumerate(control_widths):
                self.__positions.append((
                    ScreenRegion(top=current_row, left=column_pos, bottom=current_row + row_height - 1, right=column_pos + column_width - 1),
                    line[column_no][0]
                ))
                column_pos += column_width

            if available_rows == 0:
                break

            current_row += row_height

