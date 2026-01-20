import json
from pathlib import Path
import uuid

from entities.context import AppContext
from entities.entity import EntityEncoder
from entities.request import Collection, Request


class LoadError(Exception):
    pass


class PersistStore:
    __root: Path
    __collections: Path

    def __init__(self, persist_root: Path):
        self.__root = persist_root
        self.__collections = self.__root.joinpath("collections")

    def get_collection_root(self, collection: Collection):
        return self.__collections.joinpath(f"{collection.id}")

    def save_collection(self, collection: Collection, save_requests: bool = False):
        with open(self.__collections.joinpath(f"{collection.id}.json"), "w") as fp:
            json.dump(collection, fp, cls=EntityEncoder, exclude={"requests", "id"})
        
        if save_requests:
            collection_root = self.get_collection_root(collection)
            if not collection_root.is_dir():
                collection_root.mkdir(parents=True)

            # TODO: parallelize
            for request in collection.requests:
                self.save_request(collection_root, request)

    def save_request(self, collection_root: Path, request: Request):
        with open(collection_root.joinpath(f"{request.id}.json")) as fp:
            json.dump(request, fp, cls=EntityEncoder)

    def load(self) -> tuple[AppContext, ExceptionGroup | None]:
        if not self.__collections.is_dir():
            return AppContext.create(), None

        context = AppContext.create()

        errors = []
        for child in self.__collections.iterdir():
            if child.name.endswith(".json"):
                first_part = child.name.split(".")[0]
                try:
                    collection_id = uuid.UUID(first_part)
                    with open(child, "r") as fp:
                        data = json.load(fp)
                    collection = Collection(id=collection_id, **data, requests=[])
                    request_dir = self.__collections.joinpath(f"{collection.id}")
                    context.collections.append(collection)
                    if not request_dir.is_dir():
                        continue

                    requests, req_errors = PersistStore.load_requests(request_dir)
                    collection.requests = requests
                    errors.extend(req_errors)
                except Exception as exc:
                    err = LoadError("Failed to load collection from '%s'" % str(child))
                    err.__cause__ = exc
                    errors.append(err)

        return context, ExceptionGroup("Errors while loading context.", errors) if errors else None

    def ensure(self):
        if not self.__root.is_dir():
            self.__root.mkdir(parents=True)

        if not self.__collections.is_dir():
            self.__collections.mkdir(parents=True)

    @staticmethod
    def load_requests(collection_dir: Path) -> tuple[list[Request], list[LoadError]]:
        requests = []
        errors = []
        for child in collection_dir.iterdir():
            if child.name.endswith(".json"):
                first_part = child.name.split(".")[0]
                try:
                    request_id = uuid.UUID(first_part)
                    with open(child, "r") as fp:
                        data = json.load(fp)
                    request = Request(id=request_id, **data)
                    requests.append(request)
                except Exception as exc:
                    err = LoadError("Failed to load request from '%s'" % str(child))
                    err.__cause__ = exc
                    errors.append(err)
        return requests, errors

