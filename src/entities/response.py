from .entity import Entity


class Response(Entity):
    status: int
    headers: dict[str, str]
    data: bytes

