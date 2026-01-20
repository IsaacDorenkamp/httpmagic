import curses

from .control import CannotFocus, Control


class Panel(Control):
    _win: curses.window

    _location: tuple[int, int]
    _size: tuple[int, int]

    __children: list[Control]
    __content_visible: bool

    def __init__(self, parent: curses.window, location: tuple[int, int], size: tuple[int, int]):
        super().__init__()
        self._win = parent.derwin(*size, *location)
        self._win.border()
        self._win.refresh()
        self._location = location
        self._size = size
        self.__children = []
        self.__content_visible = True

    def render(self):
        self._win.border()
        if self.__content_visible:
            for child in self.__children:
                child.paint()

    def set_content_visible(self, visible: bool):
        self.__content_visible = visible
        self.repaint()

    def add_child(self, child: Control):
        self.__children.append(child)
        self.repaint()

    def remove_child(self, child: Control):
        self.__children.remove(child)
        self.repaint()

    @property
    def content_visible(self) -> bool:
        return self.__content_visible

    @property
    def pane_location(self) -> tuple[int, int]:
        return (self._location[0] + 1, self._location[1] + 1)

    @property
    def pane_size(self) -> tuple[int, int]:
        return (self._size[0] - 2, self._size[1] - 2)

    def try_focus(self):
        raise CannotFocus()

    def handle_input(self, ch: int):
        pass

    @property
    def window(self) -> curses.window:
        return self._win

