from __future__ import annotations
from abc import ABCMeta, abstractmethod
import typing


__registry = {}

def register(command, args: list[str] | None = None):
    def decorator(fn):
        __registry[command] = fn, (args or [])
        return fn
    return decorator


# built in commands
@register("new", ["name"])
def command_new(args: list[str]):
    name = args[0]


if typing.TYPE_CHECKING:
    from app import App

