from __future__ import annotations
import functools
import uuid

import framed
import framed.context
from framed.const import *
import framed.event
import framed.keys
import framed.task
from framed.widgets import *

from client import MagicClient
from entities.request import Method, Request
from entities.response import Response


class RequestView(framed.Panel):
    method_label: Label
    method: OptionBox[Method]
    url_label: Label
    url: Editor

    send: Button

    requests: framed.context.ContextRef[dict[uuid.UUID, Request]]
    responses: framed.context.ContextRef[dict[uuid.UUID, Response]]
    active_request: framed.context.ContextRef[uuid.UUID | None]
    dirty_requests: framed.context.ContextRef[set[uuid.UUID]]

    __request: Request | None
    __client: MagicClient

    def __init__(self, region: framed.rect2, owner: framed.Manager, root: framed.App):
        super().__init__(region, owner, root)
        self.__request = None
        self.__client = MagicClient()
        self.__configure()

        # context vars
        self.requests = root.context.ref("requests")
        self.responses = root.context.ref("responses")
        self.active_request = root.context.ref("active_request")
        self.dirty_requests = root.context.ref("dirty_requests")
        self.active_request.handle(self.set_request)

    def __configure(self):
        self.method_label = Label("Method: ")
        self.method_label.align = HAlign.RIGHT
        self.method = OptionBox()
        for method in Method:
            self.method.add_option(method, method)
        self.method.default = Method.GET
        self.method.foreground = Method.GET.color
        self.method.listen(framed.event.ChangeEvent, self.on_method_change)
        self.url_label = Label("URL: ")
        self.url_label.align = HAlign.RIGHT
        self.url = Editor(model_cls=LineTextModel)
        self.url.bind(framed.keys.ENTER, EditorAction.edit_finish)
        self.url.listen(framed.event.ChangeEvent, self.on_url_change)
        self.send = Button("Send", bordered=False)
        self.send.focus_foreground = "green"
        self.send.bordered = True
        self.send.listen(framed.event.ActionEvent, self.on_send)

        self.add(self.method_label)
        self.add(self.method)
        self.add(self.url_label)
        self.add(self.url)
        self.add(self.send)

    def arrange(self):
        flex = self.flex()
        flex.set_row_weight(0, 0)
        flex.set_row_weight(1, 0)
        flex.set_row_weight(2, 1)
        flex.set_row_weight(3, 0)
        flex.set_row_weight(4, 0)
        flex.add(self.method_label, row=1, weight=1)
        flex.add(self.method, row=1, weight=1)
        flex.add(self.url_label, row=1, weight=1)
        flex.add(self.url, row=1, weight=3)
        flex.add_spacer(row=3, weight=1)
        flex.add(self.send, row=3, weight=0)
        flex.add_spacer(row=3, weight=0)

    # --- Listeners ---
    def on_method_change(self, event: framed.event.ChangeEvent[OptionBoxChange]):
        self.method.foreground = event.value.label.lower()
        if self.__request is not None:
            if event.value.value and event.value.value != self.__request.method:
                self.__request.method = event.value.value
                self.__mark_dirty(self.__request.id)

    def on_url_change(self, event: framed.event.ChangeEvent[str]):
        if self.__request is not None:
            self.__request.url = event.value
            self.__mark_dirty(self.__request.id)

    def on_send(self, event: framed.event.ActionEvent):
        if self.__request is None:
            return
        task = self.root.task(self.send_request, (self.__request,))
        req_id = self.__request.id
        task.after(lambda response: self.__on_response(req_id, response))

    # --- Controllers ---
    def set_request(self, request_id: uuid.UUID | None):
        if request_id is None:
            self.method.set_option(Method.GET)
            self.url.set_text("")
        else:
            request = self.requests.get()[request_id]
            self.__request = request
            self.method.set_option(request.method, notify=True)
            self.url.set_text(request.url)

    async def send_request(self, request: Request):
        result = await self.__client.send(request)
        return Response(
            status=result.status_code,
            headers=result.headers,
            data=result.content,
        )

    def __mark_dirty(self, request_id: uuid.UUID):
        with self.dirty_requests.mutate() as dirty_requests:
            new_dirty = set(dirty_requests.value)
            new_dirty.add(request_id)
            dirty_requests.value = new_dirty

    def __on_response(self, request_id: uuid.UUID, response: Response):
        self.responses.set(self.responses.get() | {request_id: response})

