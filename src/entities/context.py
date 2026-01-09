from .entity import Entity
from .request import *


class AppContext(Entity):
    collections: list[Collection]

    # app state
    active_collection: Collection | None
    active_request: Request | None

    @staticmethod
    def create():
        return AppContext(collections=[], active_collection=None, active_request=None)
