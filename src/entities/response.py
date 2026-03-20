from .entity import Entity


class Response(Entity):
    status: int
    headers: dict[str, str]
    data: bytes
    size: int
    time: int  # time in ms

