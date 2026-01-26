from .control import CannotFocus, Container, ScreenRegion


class Panel(Container):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
            left=min(region.left + 1, region.right),
            top=min(region.top + 1, region.bottom),
            right=max(region.right - 1, region.left),
            bottom=max(region.bottom - 1, region.top)
        )

