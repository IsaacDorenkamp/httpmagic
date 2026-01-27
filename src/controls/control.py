from __future__ import annotations
from abc import ABCMeta, abstractmethod
import collections
import contextlib
import curses
import typing

import colors


class CannotFocus(NotImplementedError):
    pass


ScreenRegion = collections.namedtuple("ScreenRegion", field_names=["top", "left", "bottom", "right"])


def shift_region(a: ScreenRegion, offset: tuple[int, int]) -> ScreenRegion:
    return ScreenRegion(top=a.top + offset[0], left=a.left + offset[1], bottom=a.bottom + offset[0], right=a.right + offset[1])


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

    _size: tuple[int, int]
    _abs_pos: tuple[int, int]  # absolute screen-relative position
    _rel_pos: tuple[int, int] | None  # parent-relative position, None if no parent

    _parent: Container | None

    def __init__(self, size: tuple[int, int] = (1, 1), abs_pos: tuple[int, int] | None = None, parent: curses.window | None = None, focus_greedy: bool = False):
        # universal properties
        self._foreground = colors.get_color("foreground")
        self._background = colors.get_color("background")
        self._size = size
        self.max_size = None, None

        self.focus_greedy = focus_greedy
        self.__focused = False
        self.__visible = True

        self._parent = None
        self._rel_pos = None

        self._abs_pos = abs_pos or (0, 0)
        if parent:
            parent_pos = parent.getbegyx()
            self._win = parent.subwin(*size, *(abs_pos or parent_pos))
        else:
            self._win = curses.newwin(*size, *self._abs_pos)

        self.__pause_repaint = False
        self.__need_repaint = False
        self.__rearranging = False
        

    # Implementation-specific methods to define
    # behavior on child components.
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

    # Accessible drawing methods
    def paint(self, erase: bool = False) -> bool:
        if erase:
            self._win.erase()

        if self.__visible:
            self.render()
            self._win.refresh()
            return True

        return False

    def repaint(self):
        if self.__pause_repaint:
            self.__need_repaint = True
            return

        if not self.paint(erase=True):
            self._win.refresh()

    # Spatial Manipulation Methods
    def set_size(self, size: tuple[int, int]) -> bool:
        new_size = (
            size[0] if self.max_size[0] is None else min(self.max_size[0], size[0]),
            size[1] if self.max_size[1] is None else min(self.max_size[1], size[1]),
        )
        self._size = (
            max(1, new_size[0]),
            max(1, new_size[1]),
        )
        if not self.__rearranging:
            self._win.resize(self._size[0], self._size[1])
        return self._size == size

    def set_absolute_pos(self, abs_pos: tuple[int, int]):
        self._set_absolute_pos(abs_pos)

    def set_relative_pos(self, rel_pos: tuple[int, int]):
        if self._parent is None:
            raise ValueError("cannot set relative position of parentless control")

        parent_absolute_pos = self._parent.absolute_pos
        self._rel_pos = rel_pos
        self._set_absolute_pos((parent_absolute_pos[0] + rel_pos[0], parent_absolute_pos[1] + rel_pos[1]), _update_rel=False)

    # Internal API functions for use by subclasses
    def _erase(self):
        self._win.erase()

    def _set_absolute_pos(self, abs_pos: tuple[int, int], _update_rel: bool = True):
        self._erase()
        if self._parent is not None and _update_rel:
            parent_abs_pos = self._parent.absolute_pos
            self._rel_pos = (
                parent_abs_pos[0] - abs_pos[0],
                parent_abs_pos[1] - abs_pos[1]
            )
        self._abs_pos = abs_pos
        self._win.mvwin(*abs_pos)
        self.repaint()

    @property
    def size(self) -> tuple[int, int]:
        return self._size

    @property
    def absolute_pos(self) -> tuple[int, int]:
        return self._abs_pos

    @property
    def relative_pos(self) -> tuple[int, int]:
        if self._rel_pos is None:
            raise ValueError("cannot get relative position of parentless control")

        return self._rel_pos

    @property
    def focused(self) -> bool:
        return self.__focused

    @property
    def foreground(self):
        return self._foreground

    @foreground.setter
    def foreground(self, value: int):
        self._foreground = value
        self._win.bkgd(colors.color_pair(self.foreground, self.background))
        self._win.refresh()

    @property
    def background(self):
        return self._background

    @background.setter
    def background(self, value: int):
        self._background = value
        self._win.bkgd(colors.color_pair(self.foreground, self.background))
        self._win.refresh()

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
            self._win.resize(*self._size)
            self.repaint()

    def set_visible(self, visible: bool):
        self.__visible = visible
        self.repaint()

    @property
    def visible(self) -> bool:
        return self.__visible

    @property
    def parent(self) -> Container | None:
        return self._parent

    # TODO: cache this property?
    @property
    def screen_region(self) -> ScreenRegion:
        return ScreenRegion(*(self.absolute_pos + (self.absolute_pos[0] + self.size[0] - 1, self.absolute_pos[1] + self.size[1] - 1)))


class Container(Control):
    _children: list[Control]
    __layout: Layout | None
    __content_visible: bool

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._children = []
        self.__layout = None
        self.__content_visible = True

    def add(self, control: Control):
        if control._parent is not None:
            raise ValueError("control '%s' already belongs to a container!" % str(control))

        self._children.append(control)
        control._parent = self
        control.set_relative_pos((0, 0))

    def remove(self, control: Control):
        self._children.remove(control)
        control._parent = None
        control._rel_pos = None

    def paint(self, erase: bool = False):
        if erase:
            self._win.erase()
            self._win.refresh()

        if self.visible:
            self.render()

        return True

    def render(self):
        if self.__content_visible:
            for child in self._children:
                child.repaint()

    def set_size(self, size: tuple[int, int]) -> bool:
        result = super().set_size(size)

        # constrain children to this container's screen region (top, left, bottom, right)
        for child in self._children:
            self._constrain(child)

        self._relayout()

        return result

    def set_layout(self, layout: Layout | None):
        self.__layout = layout
        self._relayout()

    def _constrain(self, child: Control):
        screen_region = self.screen_region
        child_region = child.screen_region
        
        new_region = (
            min(screen_region[2], max(screen_region[0], child_region[0])),
            min(screen_region[3], max(screen_region[1], child_region[1])),
            max(screen_region[0], min(screen_region[2], child_region[2])),
            max(screen_region[1], min(screen_region[3], child_region[3]))
        )
        new_size = (new_region[2] - new_region[0]) + 1, (new_region[3] - new_region[1]) + 1
        new_pos  = new_region[0], new_region[1]
        with child.rearrange():
            child.set_size(new_size)
            child.set_absolute_pos(new_pos)

    def set_absolute_pos(self, abs_pos: tuple[int, int]):
        # adjust children based on relative pos
        for child in self._children:
            rel_pos = child.relative_pos
            child._set_absolute_pos((abs_pos[0] + rel_pos[0], abs_pos[1] + rel_pos[1]), _update_rel=False)
        super().set_absolute_pos(abs_pos)
        self._relayout()

    @contextlib.contextmanager
    def rearrange(self):
        with super().rearrange():
            yield
        self._relayout()

    def _relayout(self):
        if self.__layout:
            self.__layout.arrange(self.content_region)

    def set_content_visible(self, visible: bool):
        self.__content_visible = visible
        self.repaint()

    @property
    def content_visible(self) -> bool:
        return self.__content_visible

    @property
    def content_region(self) -> ScreenRegion:
        return self.screen_region

    @property
    def content_size(self) -> tuple[int, int]:
        region = self.content_region
        return region.bottom - region.top + 1, region.right - region.left + 1


if typing.TYPE_CHECKING:
    from .layout import Layout

