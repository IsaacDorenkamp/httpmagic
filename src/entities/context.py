import uuid

from .entity import Entity
from .request import *
from .response import *
from .settings import Settings


class AppContextEntity(Entity):
    # config stuff
    settings: Settings

    # workspace
    collections: list[Collection]

    @staticmethod
    def create():
        return AppContextEntity(settings=Settings(), collections=[])

