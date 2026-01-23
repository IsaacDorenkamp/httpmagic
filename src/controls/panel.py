import contextlib
import curses

from .control import CannotFocus, Control
from controls.layout import Layout


class Panel(Control):
    __children: list[Control]
    __content_visible: bool
    __layout: Layout | None

    def __init__(self, parent: curses.window, location: tuple[int, int], size: tuple[int, int]):
        super().__init__()
        self._create_window(parent, size, location)
        self._win.border()
        self._win.refresh()
        self.__children = []
        self.__content_visible = True
        self.__layout = None

    def set_layout(self, layout: Layout | None):
        self.__layout = layout
        if self.__layout:
            self.__layout.arrange(self._win)
            self.repaint()

    def render(self):
        self._win.box()
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
        return (self._pos[0] + 1, self._pos[1] + 1)

    @property
    def pane_size(self) -> tuple[int, int]:
        return (self._size[0] - 2, self._size[1] - 2)

    def try_focus(self):
        raise CannotFocus()

    def handle_input(self, ch: int):
        pass

    @contextlib.contextmanager
    def rearrange(self):
        with super().rearrange():
            yield
        if self.__layout:
            import logging
            logging.debug("REARRANGE")
            self.__layout.arrange(self._win)
            self.repaint()

    @property
    def window(self) -> curses.window:
        return self._win

