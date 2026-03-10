import enum
import typing
import uuid


class SetRequest(typing.TypedDict):
    request: uuid.UUID | None


class MessageType(enum.StrEnum):
    set_request = "set_request"

