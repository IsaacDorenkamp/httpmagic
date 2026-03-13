from __future__ import annotations
import uuid

import framed
import framed.context
from framed.widgets import *

from entities.response import Response


class ResponseView(framed.Panel):
    active_request: framed.context.ContextRef[uuid.UUID | None]
    responses: framed.context.ContextRef[dict[uuid.UUID, Response]]

    response: Editor

    def __init__(self, region: framed.rect2, owner: framed.Manager, root: framed.App):
        super().__init__(region, owner, root)
        self.active_request = root.context.ref("active_request")
        self.responses = root.context.ref("responses")

        self.active_request.handle(self.on_request_changed)
        self.responses.handle(self.on_responses_changed)

        self.response = Editor()
        self.response.editable = False
        self.add(self.response)

    def arrange(self):
        grid = self.grid()
        grid.add(self.response, 0, 0)

    # --- Controllers ---
    def on_request_changed(self, request: uuid.UUID | None):
        self.__update(request, None)

    def on_responses_changed(self, responses: dict[uuid.UUID, Response]):
        self.__update(None, responses)

    def __update(self, request: uuid.UUID | None, responses: dict[uuid.UUID, Response] | None):
        if responses is not None:
            request = self.active_request.get()
            if request:
                response = responses.get(request)
                if response is not None:
                    self.response.set_text(response.data.decode('utf-8'))
                else:
                    self.response.set_text("")
            else:
                self.response.set_text("")
        elif request is not None:
            responses = self.responses.get()
            response = responses.get(request)
            if response is not None:
                self.response.set_text(response.data.decode('utf-8'))
            else:
                self.response.set_text("")
        else:
            self.response.set_text("")

