from __future__ import annotations
import typing

from controls import Panel

if typing.TYPE_CHECKING:
    from ..app import App


class ResponseView(Panel):
    def __init__(self, parent: App, pos: tuple[int, int], size: tuple[int, int]):
        super().__init__(parent.stdscr, pos, size)

