from abc import ABCMeta, abstractmethod
import contextlib
import curses
import typing

import colors


class CannotFocus(NotImplementedError):
    pass


class Control(metaclass=ABCMeta):
    CTRL_B: typing.ClassVar[int] = 2
    CTRL_C: typing.ClassVar[int] = 3
    CTRL_E: typing.ClassVar[int] = 5
    CTRL_S: typing.ClassVar[int] = 19

    ESC = 27
    RETURN = ord('\n')

    __focused: bool
    _win: curses.window

    _foreground: int
    _background: int

    __pause_repaint: bool
    __need_repaint: bool
    __rearranging: bool

    __visible: bool

    focus_greedy: bool  # Refuses attempts to wrest focus.

    max_size: tuple[int | None, int | None]

    def __init__(self, focus_greedy: bool = False):
        self.__focused = False
        self._foreground = Control.g_foreground
        self._background = Control.g_background

        self.__pause_repaint = False
        self.__need_repaint = False
        self.__rearranging = False
        self.__visible = True
        self.focus_greedy = focus_greedy
        self.max_size = None, None

    def _create_window(self, parent: curses.window, size: tuple[int, int], pos: tuple[int, int]):
        win = parent.derwin(*size, *pos)
        win.bkgd(colors.color_pair(self.foreground, self.background))
        win.refresh()
        self._size = size
        self._pos = pos
        self._win = win

    def try_focus(self):
        """
        Try to accept focus. If this component
        cannot accept focus, this function
        should raise CannotFocus.
        """
        pass

    def focus(self):
        """
        Attempt to grant focus to this control.
        If the control cannot accept focus, then
        this function should raise CannotFocus.
        """
        if not self.__focused:
            try:
                self.try_focus()
                self.__focused = True
                self.on_focus()
            except CannotFocus:
                pass

    def on_unfocus(self):
        """
        What to do before focus is revoked from
        this control.
        """
        pass

    def on_focus(self):
        """
        What to do when focus is granted to
        this control.
        """
        pass

    def unfocus(self):
        """
        Attempt to revoke focus from this control.
        Defaults to doing nothing.
        """
        if self.__focused:
            self.on_unfocus()
            self.__focused = False

    @abstractmethod
    def handle_input(self, ch: int):
        raise NotImplementedError()

    @abstractmethod
    def render(self):
        """
        While controls should be designed to re-render as little as possible, there are
        situations where any control must be able to fully paint its contents when
        requested to do so.
        """
        raise NotImplementedError()

    def paint(self) -> bool:
        if self.__visible:
            self.render()
            self._win.refresh()
            return True

        return False

    def repaint(self):
        if self.__pause_repaint:
            self.__need_repaint = True
            return

        self._win.erase()
        if not self.paint():
            self._win.refresh()

    def set_size(self, size: tuple[int, int]) -> bool:
        self._size = (
            size[0] if self.max_size[0] is None else min(self.max_size[0], size[0]),
            size[1] if self.max_size[1] is None else min(self.max_size[1], size[1]),
        )
        if not self.__rearranging:
            self._win.resize(*size)
        return self._size == size

    def set_pos(self, pos: tuple[int, int]):
        self._pos = pos
        self._win.mvderwin(*pos)

    @property
    def focused(self) -> bool:
        return self.__focused

    g_foreground: typing.ClassVar[int] = -1
    g_background: typing.ClassVar[int] = -1

    @classmethod
    def configure(
        cls,
        foreground: int,
        background: int,
    ):
        cls.g_foreground = foreground
        cls.g_background = background

    @property
    def foreground(self):
        return self._foreground

    @foreground.setter
    def foreground(self, value: int):
        self._foreground = value
        self._win.bkgd(colors.color_pair(self.foreground, self.background))
        self.repaint()

    @property
    def background(self):
        return self._background

    @background.setter
    def background(self, value: int):
        self._background = value
        self._win.bkgd(colors.color_pair(self.foreground, self.background))
        self.repaint()

    @contextlib.contextmanager
    def usecolor(self, window: curses.window, color_pair: int | None = None):
        base = colors.color_pair(self.foreground, self.background)
        attr = color_pair if color_pair is not None else base
        try:
            window.attron(attr)
            yield
        finally:
            window.attroff(attr)

    @contextlib.contextmanager
    def no_repaint(self):
        self.__pause_repaint = True
        try:
            yield
        finally:
            self.__pause_repaint = False
            if self.__need_repaint:
                self.__need_repaint = False
                self.repaint()

    @contextlib.contextmanager
    def rearrange(self):
        self.__rearranging = True
        self._win.resize(1, 1)
        try:
            yield
        finally:
            self.__rearranging = False
            import logging
            logging.debug(f"setting size to {self._size}")
            self._win.resize(*self._size)
            self._win.refresh()

    def invert_colors(self):
        temp = self._foreground
        self._foreground = self._background
        self._background = temp
        self._win.bkgd(colors.color_pair(self.foreground, self.background))
        self.repaint()

    def set_visible(self, visible: bool):
        self.__visible = visible
        self.repaint()

    @property
    def visible(self) -> bool:
        return self.__visible

