import enum
import uuid

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
    def color(self) -> str:
        match self:
            case Method.GET:
                return "green"
            case Method.HEAD:
                return "magenta"
            case Method.POST:
                return "yellow"
            case Method.PUT:
                return "blue"
            case Method.DELETE:
                return "red"
            case Method.PATCH:
                return "cyan"
            case Method.OPTIONS:
                return "white"


class Request(Entity):
    name: str
    id: uuid.UUID
    parent: uuid.UUID | None

    method: Method
    url: str
    headers: dict[str, str]


class Collection(Entity):
    name: str
    id: uuid.UUID
    requests: list[Request]

