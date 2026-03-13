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
    collections: dict[str, Collection]
    requests: dict[uuid.UUID, Request]
    responses: dict[uuid.UUID, Response]
    active_collection: str | None
    active_request: uuid.UUID | None

    def __init__(self):
        super().__init__()
        self.create_var("collections", {}, dict)
        self.create_var("requests", {}, dict)
        self.create_var("responses", {}, dict)
        self.create_var("active_collection", None, str)
        self.create_var("active_request", None, uuid.UUID)

    def conform(self, entity: AppContextEntity):
        collections = {}
        requests = {}
        for collection in entity.collections:
            collections[collection.name] = collection
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
        self.set_task_callback(self.task_callback)
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
            ordered_names = sorted(self.context.collections.keys())
            self.context.active_collection = ordered_names[0]
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

        request = Request(name=name, id=uuid.uuid4(), method=Method.GET, url="", headers={})
        with self.context.mutate("collections") as collections:
            collection: Collection = collections.value[active_collection]
            if name in [request.name for request in collection.requests]:
                collections.cancel()
                raise ValueError(f"Collection '{collection.name}' already has a request named '{name}'")
            collection.requests.append(request)

        with self.context.mutate("requests") as requests:
            requests.value[request.id] = request.copy()

        if activate:
            with self.context.mutate("active_request") as active_request:
                active_request.value = request.id

    def create_collection(self, name: str, activate: bool = False):
        if name in [collection.name for collection in self.context.collections.values()]:
            raise ValueError(f"A collection named '{name}' already exists.")

        collection = Collection(name=name, id=uuid.uuid4(), requests=[])
        with self.context.mutate("collections") as collections:
            collections.value[collection.name] = collection

        if activate:
            with self.context.mutate("active_collection") as active_collection:
                active_collection.value = name

