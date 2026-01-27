import colors
from .control import CannotFocus, Container, ScreenRegion
import util


class Panel(Container):
    padding: tuple[int, int]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.padding = 0, 0

    def handle_input(self, ch: int):
        pass

    def render(self):
        self._win.border()
        self._win.refresh()
        super().render()

    def try_focus(self):
        raise CannotFocus()

    @property
    def content_region(self) -> ScreenRegion:
        region = self.screen_region
        return ScreenRegion(
            left=min(region.left + 1 + self.padding[1], region.right),
            top=min(region.top + 1 + self.padding[0], region.bottom),
            right=max(region.right - 1 - self.padding[1], region.left),
            bottom=max(region.bottom - 1 - self.padding[0], region.top)
        )


class TitledPanel(Panel):
    def __init__(self, title: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__title = title

    def render(self):
        super().render()
        self.__draw_title(True)

    def __draw_title(self, refresh: bool = False):
        self._win.move(0, 0)
        self._win.addch('\u250C')
        self._win.addstr('\u2500' * (self._size[1] - 2))
        self._win.addch('\u2510')
        self._win.move(0, 1)
        title = util.ellipsize(self.__title, self._size[1] - 4)
        pair = colors.color_pair(self.background, self.foreground)
        self._win.addch(' ', pair)
        self._win.addnstr(title, self._size[1] - 4, pair)
        if len(title) < self._size[1]:
            self._win.addch(' ', pair)

        if refresh:
            self._win.refresh()

    def set_title(self, title: str):
        self.__title = title
        self.__draw_title(refresh=True)

    @property
    def title(self) -> str:
        return self.__title

