import curses

from controls.panel import Panel


class RequestView(Panel):
    def __init__(self, parent: curses.window, pos: tuple[int, int], size: tuple[int, int]):
        super().__init__(parent, pos, size)

    def render(self):
        super().render()
