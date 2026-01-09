import enum

from .entity import Entity


class Method(enum.StrEnum):
    GET = "GET"
    HEAD = "HEAD"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    OPTIONS = "OPTIONS"


class Request(Entity):
    name: str

    method: Method
    url: str
    headers: dict[str, str]


class Collection(Entity):
    name: str
    requests: list[Request]

