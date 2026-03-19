import enum
import logging
import traceback
import typing
import uuid

import framed
import framed.context
import framed.palette
import framed.task
from framed import keys

from entities.context import AppContextEntity
from entities.settings import Settings
from entities.request import Collection, Method, Request
from entities.response import Response
from persist import PersistStore

from views.collection_view import CollectionView
from views.command_view import CommandView
from views.request_view import RequestView
from views.response_view import ResponseView


class AppAction(enum.Enum):
    collections_focus = "collections_focus"

    request_method = "request_method"
    request_url = "request_url"
    request_send = "request_send"

    command_focus = "command_focus"


class AppContext(framed.context.Context):
    collections: dict[uuid.UUID, Collection]
    requests: dict[uuid.UUID, Request]
    responses: dict[uuid.UUID, Response]
    errors: dict[uuid.UUID, BaseException]
    active_collection: uuid.UUID | None
    active_request: uuid.UUID | None
    dirty_requests: set[uuid.UUID]
    dirty_collections: set[uuid.UUID]

    def __init__(self):
        super().__init__()
        self.create_var("collections", {}, dict)
        self.create_var("requests", {}, dict)
        self.create_var("responses", {}, dict)
        self.create_var("errors", {}, dict)
        self.create_var("active_collection", None, uuid.UUID)
        self.create_var("active_request", None, uuid.UUID)
        self.create_var("dirty_requests", set(), set)
        self.create_var("dirty_collections", set(), set)

    def conform(self, entity: AppContextEntity):
        collections = {}
        requests = {}
        for collection in entity.collections:
            collections[collection.id] = collection
            for request in collection.requests:
                requests[request.id] = request
        self.collections = collections
        self.requests = requests

    def entity(self) -> AppContextEntity:
        return AppContextEntity(
            settings=Settings(),
            collections=list(self.collections.values()),
        )


class App(framed.App[AppContext]):
    _DEFAULT_BINDINGS: dict[int, AppAction] = {
        keys.C: AppAction.collections_focus,
        keys.M: AppAction.request_method,
        keys.U: AppAction.request_url,
        keys.S: AppAction.request_send,
        keys.COLON: AppAction.command_focus,
    }

    collection_view: CollectionView
    command_view: CommandView
    request_view: RequestView
    response_view: ResponseView

    store: PersistStore

    __bindings: dict[int, AppAction]

    def __init__(self, stdscr, context: AppContextEntity, store: PersistStore):
        super().__init__(stdscr, context_cls=AppContext)
        self.store = store
        self.context.conform(context)
        self.__bindings = App._DEFAULT_BINDINGS.copy()
        self.set_control_handler(self.on_input)
        self.__make_colors()
        self.__configure()

    def __make_colors(self):
        for method in Method:
            framed.palette.alias(method.color, method.lower())

    def __configure(self):
        manager = self.multiplex()
        app_split, command_split = manager.split(2, direction=framed.Direction.vertical)
        collection_split, request_split, response_split = manager.split(3, path=app_split, direction=framed.Direction.horizontal)

        manager.set_proportions((), (1, 0))
        manager.set_proportions(app_split, (1, 2, 2))
        manager.set_min_size(command_split, 2)

        self.collection_view = self.new_panel(CollectionView, split_path=collection_split)
        self.command_view = self.new_panel(CommandView, split_path=command_split)
        self.request_view = self.new_panel(RequestView, split_path=request_split)
        self.response_view = self.new_panel(ResponseView, split_path=response_split)

        if self.context.collections:
            alpha_first = sorted(self.context.collections.values(), key=lambda collection: collection.name)[0]
            self.context.active_collection = alpha_first.id  # FIX: this sucks
            collection = self.context.collections[self.context.active_collection]
            if collection.requests:
                request = collection.requests[0]
                self.context.active_request = request.id

    # --- Controllers ---
    def on_input(self, ch: int):
        action = self.__bindings.get(ch)
        if action is not None:
            match action:
                case AppAction.collections_focus:
                    self.focus(self.collection_view.requests)
                case AppAction.request_method:
                    self.focus(self.request_view.method)
                case AppAction.request_url:
                    self.focus(self.request_view.url)
                case AppAction.request_send:
                    self.focus(self.request_view.send)
                case AppAction.command_focus:
                    self.focus(self.command_view.command)
                    return framed.FocusCapture.passthrough  # trick to pass the colon press to the editor
            return framed.FocusCapture.capture

    def task_callback(self, task_id: int, status: framed.task.TaskStatus, info: typing.Any):
        if isinstance(info, Exception):
            formatted = "".join(traceback.format_exception(info)).split("\n")
            for line in formatted:
                logging.error(line)

    # --- Public API ---
    def create_request(self, name: str, activate: bool = False):
        active_collection = self.context.active_collection
        if active_collection is None:
            raise ValueError("No collection is active.")

        request = Request(name=name, id=uuid.uuid4(), parent=active_collection, method=Method.GET, url="", headers={})
        with self.context.mutate("collections") as collections:
            collection: Collection = collections.value[active_collection]
            if name in [request.name for request in collection.requests]:
                collections.cancel()
                raise ValueError(f"Collection '{collection.name}' already has a request named '{name}'")
            collection.requests.append(request)

        with self.context.mutate("requests") as requests, self.context.mutate("dirty_requests") as dirty_requests:
            requests.value[request.id] = request.copy()
            new_dirty = set(dirty_requests.value)
            new_dirty.add(request.id)
            dirty_requests.value = new_dirty

        if activate:
            self.context.active_request = request.id

    def create_collection(self, name: str, activate: bool = False):
        if name in [collection.name for collection in self.context.collections.values()]:
            raise ValueError(f"A collection named '{name}' already exists.")

        collection = Collection(name=name, id=uuid.uuid4(), requests=[])
        self.context.collections = self.context.collections | {collection.id: collection}

        if activate:
            self.context.active_collection = collection.id

    def set_active_collection(self, name: str):
        collection = next((collection for collection in self.context.collections.values() if collection.name == name), None)
        if collection is None:
            raise ValueError(f"No collection '{name}'")

        self.context.active_collection = collection.id
        self.context.active_request = sorted(collection.requests, key=lambda request: request.name)[0].id if collection else None

    def set_active_request(self, request: uuid.UUID | None, sync_parent: bool = False):
        if request is not None and request not in self.context.requests.keys():
            raise ValueError(f"No request with id '{request}'")

        req = self.context.requests.get(request) if request else None
        if req is not None:
            new_id = req.id
            collection = req.parent if sync_parent else None
        else:
            new_id = None
            collection = None

        self.context.active_request = new_id
        if collection is not None:
            self.context.active_collection = collection

    def rename_active_request(self, name: str):
        active_request = self.context.active_request
        if active_request is None:
            raise ValueError("No request is currently active.")

        with (
            self.context.mutate("requests") as requests,
            self.context.mutate("collections") as collections,
            self.context.mutate("dirty_requests") as dirty_requests
        ):
            new_req = requests.value[active_request].copy()
            if name == new_req.name:
                # ignore
                raise ValueError("Name did not change!")
            new_req.name = name
            requests.value = requests.value | {new_req.id: new_req}
            dirty_requests.value = dirty_requests.value | {new_req.id}

            if new_req.parent is None:
                # if this is a free-floating request, don't update collections
                return

            # update collection
            existing = collections.value.get(new_req.parent)
            if existing is None:
                requests.cancel()
                collections.cancel()
                return
            new_collection = existing.copy()
            new_collection.requests = [request if request.id != new_req.id else new_req for request in new_collection.requests]
            collections.value = collections.value | {new_collection.name: new_collection}

    def save_active_request(self):
        active_request = self.context.active_request
        if active_request is None:
            raise ValueError("No request is currently active.")

        request = self.context.requests[active_request]
        collection = self.context.collections.get(request.parent) if request.parent else None
        if collection is None:
            raise ValueError("Request has no parent collection!")
        self.store.save_request(self.store.get_collection_root(collection), request)

        with self.context.mutate("dirty_requests") as dirty_requests:
            new_dirty = set(dirty_requests.value)
            if request.id in dirty_requests.value:
                new_dirty.remove(request.id)
                dirty_requests.value = new_dirty
            else:
                dirty_requests.cancel()

    def rename_active_collection(self, name: str):
        active_collection = self.context.active_collection
        if active_collection is None:
            raise ValueError("No collection is currently active.")

        if name in [collection.name for collection in self.context.collections.values() if collection.id != active_collection]:
            raise ValueError("A collection with that name already exists!")

        with (
            self.context.mutate("dirty_collections") as dirty_collections,
            self.context.mutate("collections") as collections,
        ):
            if name == collections.value[active_collection].name:
                collections.cancel()
                dirty_collections.cancel()
                return
            new_collection = collections.value[active_collection].copy()
            new_collection.name = name
            new_collections = dict(collections.value)
            new_collections[new_collection.id] = new_collection
            collections.value = new_collections
            dirty_collections.value = dirty_collections.value | {new_collection.id}

    def save_active_collection(self):
        active_collection = self.context.active_collection
        if active_collection is None:
            raise ValueError("No collection is currently active.")

        collection = self.context.collections[active_collection]
        self.store.save_collection(collection)

        with self.context.mutate("dirty_collections") as dirty_collections:
            new_dirty = set(dirty_collections.value)
            if collection.id in new_dirty:
                new_dirty.remove(collection.id)
                dirty_collections.value = new_dirty
            else:
                dirty_collections.cancel()

