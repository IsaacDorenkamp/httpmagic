import curses
import enum

import colors
from .entity import Entity


class Method(enum.StrEnum):
    GET = "GET"
    HEAD = "HEAD"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    OPTIONS = "OPTIONS"

    @property
    def color(self) -> int:
        match self:
            case Method.GET:
                return curses.COLOR_GREEN
            case Method.HEAD:
                return curses.COLOR_MAGENTA
            case Method.POST:
                return curses.COLOR_YELLOW
            case Method.PUT:
                return curses.COLOR_BLUE
            case Method.DELETE:
                return curses.COLOR_RED
            case Method.PATCH:
                return curses.COLOR_CYAN
            case Method.OPTIONS:
                return colors.COLOR_ORANGE


class Request(Entity):
    name: str

    method: Method
    url: str
    headers: dict[str, str]


class Collection(Entity):
    name: str
    requests: list[Request]

