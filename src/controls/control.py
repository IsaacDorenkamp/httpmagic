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

    ESC = 27
    RETURN = ord('\n')

    __focused: bool
    _win: curses.window

    _foreground: int
    _background: int

    __pause_repaint: bool
    __need_repaint: bool

    focus_greedy: bool  # Refuses attempts to wrest focus.

    def __init__(self, focus_greedy: bool = False):
        self.__focused = False
        self._foreground = Control.g_foreground
        self._background = Control.g_background

        self.__pause_repaint = False
        self.__need_repaint = False
        self.focus_greedy = focus_greedy

    def _create_window(self, parent: curses.window, size: tuple[int, int], pos: tuple[int, int]):
        win = parent.derwin(*size, *pos)
        win.bkgd(colors.color_pair(self.foreground, self.background))
        win.refresh()
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

    def repaint(self):
        if self.__pause_repaint:
            self.__need_repaint = True
            return

        self._win.erase()
        self.render()
        self._win.refresh()

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

    def invert_colors(self):
        temp = self._foreground
        self._foreground = self._background
        self._background = temp
        self._win.bkgd(colors.color_pair(self.foreground, self.background))
        self.repaint()

