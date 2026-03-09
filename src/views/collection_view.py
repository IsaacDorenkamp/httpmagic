import typing

import framed
from framed.widgets import *

class CollectionView(framed.Panel):
    collection: Label
    requests: ListBox

    def __init__(self, region: framed.rect2, owner: framed.Manager):
        super().__init__(region, owner)
        self.collection = Label("collection")
        self.collection.bold = True
        self.collection.italic = True
        self.collection.underline = True

        self.requests = ListBox()

        self.add(self.collection)
        self.add(self.requests)

    def arrange(self):
        flex = self.flex()
        flex.set_row_weight(0, 0)
        flex.set_row_weight(1, 1)
        flex.add(self.collection, row=0, weight=1)
        flex.add(self.requests, row=1, weight=1)

    def set_name(self, name: str):
        self.collection.set_text(name)

    def set_requests(self, requests: typing.Iterable[str]):
        self.requests.clear()
        for request in sorted(requests):
            self.requests.add_item(request, request)

    def set_selected_request(self, request: str):
        index = self.requests.find_item(request)
        if index >= 0:
            self.requests.set_selection(index)

