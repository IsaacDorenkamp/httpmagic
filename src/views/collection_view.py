import uuid

import framed
from framed.const import *
import framed.event
from framed import keys
from framed.widgets import *

from entities.request import Collection
from typedefs import MessageType, SetRequest


class CollectionView(framed.Panel):
    collection: Label
    requests: ListBox

    def __init__(self, region: framed.rect2, owner: framed.Manager):
        super().__init__(region, owner)
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

    def arrange(self):
        flex = self.flex()
        flex.set_row_weight(0, 0)
        flex.set_row_weight(1, 1)
        flex.add(self.collection, row=0, weight=1)
        flex.add(self.requests, row=1, weight=1)

    def set_collection(self, collection: Collection):
        self.collection.set_text(collection.name)
        self.requests.clear()
        for request in sorted(collection.requests, key=lambda r: r.name):
            self.requests.add_item(request.name, request.id)

    def set_selected_request(self, request: str):
        index = self.requests.find_item(request)
        if index >= 0:
            self.requests.set_selection(index)

    def on_change(self, event: framed.event.ChangeEvent[ListBoxChange[uuid.UUID]]):
        if event.value.value:
            req_id = event.value.value
        else:
            req_id = None
        self.broadcast(MessageType.set_request, { "request": req_id })

