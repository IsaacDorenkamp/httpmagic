import uuid

import framed
import framed.context
from framed.const import *
import framed.event
from framed import keys
from framed.widgets import *

from entities.request import Collection


class CollectionView(framed.Panel):
    collection: Label
    requests: ListBox

    collections: framed.context.ContextRef[dict[uuid.UUID, Collection]]
    active_collection: framed.context.ContextRef[uuid.UUID | None]
    active_request: framed.context.ContextRef[uuid.UUID | None]
    dirty_requests: framed.context.ContextRef[set[uuid.UUID]]
    dirty_collections: framed.context.ContextRef[set[uuid.UUID]]

    def __init__(self, region: framed.rect2, owner: framed.Manager, root: framed.App):
        super().__init__(region, owner, root)
        self.collection = Label("Collection")
        self.collection.bold = True
        self.collection.italic = True
        self.collection.underline = True
        self.collection.extend = True

        self.requests = ListBox()
        self.requests.bind(keys.j, ListBoxAction.nav_down)
        self.requests.bind(keys.k, ListBoxAction.nav_up)
        self.requests.listen(framed.event.ChangeEvent, self.on_change)

        self.add(self.collection)
        self.add(self.requests)

        self.collections = root.context.ref("collections")
        self.active_collection = root.context.ref("active_collection")
        self.active_request = root.context.ref("active_request")
        self.dirty_requests = root.context.ref("dirty_requests")
        self.dirty_collections = root.context.ref("dirty_collections")
        self.collections.handle(self.on_collections_changed)
        self.active_collection.handle(self.on_active_collection_changed)
        self.active_request.handle(self.on_active_request_changed)
        self.dirty_requests.handle(self.on_dirty_requests_changed)
        self.dirty_collections.handle(self.on_dirty_collections_change)

    def arrange(self):
        flex = self.flex()
        flex.set_row_weight(0, 0)
        flex.set_row_weight(1, 1)
        flex.add(self.collection, row=0, weight=1)
        flex.add(self.requests, row=1, weight=1)

    def set_collection(self, collection: Collection):
        self.collection.set_text(f"{collection.name} *" if collection.id in self.dirty_collections.get() else collection.name)
        self.requests.clear()
        dirty_requests = self.dirty_requests.get()
        for request in sorted(collection.requests, key=lambda r: r.name):
            is_dirty = request.id in dirty_requests
            self.requests.add_item(f"{request.name} *" if is_dirty else request.name, request.id)

        active_request = self.active_request.get()
        if active_request is not None:
            index = self.requests.find_item(active_request)
            self.requests.set_selection(index)

    def set_selected_request(self, request: str):
        index = self.requests.find_item(request)
        if index >= 0:
            self.requests.set_selection(index)

    def on_change(self, event: framed.event.ChangeEvent[ListBoxChange[uuid.UUID]]):
        if event.value.value:
            req_id = event.value.value
        else:
            req_id = None
        self.root.context.active_request = req_id

    def on_active_collection_changed(self, new_collection_id: uuid.UUID | None):
        if new_collection_id is not None:
            collection = self.root.context.collections.get(new_collection_id)
            if collection:
                self.set_collection(collection)
        else:
            self.requests.clear()

    def on_active_request_changed(self, request_id: uuid.UUID | None):
        if request_id is None:
            self.requests.set_selection(-1)
        else:
            index = self.requests.find_item(request_id)
            self.requests.set_selection(index)

    def on_collections_changed(self, collections: dict[uuid.UUID, Collection]):
        active_collection = self.active_collection.get()
        if active_collection is not None:
            self.set_collection(collections[active_collection])

    def on_dirty_requests_changed(self, dirty_requests: set[uuid.UUID]):
        for index in range(self.requests.count):
            req_text, req_id = self.requests.get_item_pair(index)
            if req_id in dirty_requests and not req_text.endswith(" *"):
                self.requests.set_item_text(index, f"{req_text} *")
            elif req_id not in dirty_requests and req_text.endswith(" *"):
                self.requests.set_item_text(index, req_text[:-2])

    def on_dirty_collections_change(self, dirty_collections: set[uuid.UUID]):
        active_collection = self.active_collection.get()
        collection = self.root.context.collections[active_collection]
        if active_collection in dirty_collections:
            self.collection.set_text(f"{collection.name} *")
        else:
            self.collection.set_text(collection.name)

