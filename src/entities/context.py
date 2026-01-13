from .entity import Entity
from .request import *
from .settings import Settings


class AppContext(Entity):
    # config stuff
    settings: Settings

    # workspace
    collections: list[Collection]

    # app state
    active_collection: Collection | None
    active_request: Request | None


    @staticmethod
    def create():
        return AppContext(settings=Settings(), collections=[], active_collection=None, active_request=None)
