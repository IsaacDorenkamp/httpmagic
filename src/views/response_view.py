from __future__ import annotations
import uuid

import framed
import framed.context
from framed.widgets import *

from entities.response import Response


class ResponseView(framed.Panel):
    active_request: framed.context.ContextRef[uuid.UUID | None]
    errors: framed.context.ContextRef[dict[uuid.UUID, BaseException]]
    responses: framed.context.ContextRef[dict[uuid.UUID, Response]]

    response: Editor

    def __init__(self, region: framed.rect2, owner: framed.Manager, root: framed.App):
        super().__init__(region, owner, root)
        self.active_request = root.context.ref("active_request")
        self.errors = root.context.ref("errors")
        self.responses = root.context.ref("responses")

        self.active_request.handle(self.on_request_changed)
        self.errors.handle(self.on_errors_changed)
        self.responses.handle(self.on_responses_changed)

        self.response = Editor()
        self.response.editable = False
        self.add(self.response)

    def arrange(self):
        grid = self.grid()
        grid.add(self.response, 0, 0)

    # --- Controllers ---
    def on_request_changed(self, request: uuid.UUID | None):
        self.__update(request=request)

    def on_errors_changed(self, errors: dict[uuid.UUID, BaseException]):
        self.__update(errors=errors)

    def on_responses_changed(self, responses: dict[uuid.UUID, Response]):
        self.__update(responses=responses)

    def __update(self, request: uuid.UUID | None = None, responses: dict[uuid.UUID, Response] | None = None, errors: dict[uuid.UUID, BaseException] | None = None):
        if responses is not None:
            request = self.active_request.get()
            response = None
            error = None
            if request:
                response = responses.get(request)
                error = self.errors.get().get(request)
            self.__update_editor_content(request, response, error)
        elif request is not None:
            responses = self.responses.get()
            errors = self.errors.get()
            response = responses.get(request)
            error = errors.get(request)
            self.__update_editor_content(request, response, error)
        elif errors is not None:
            request = self.active_request.get()
            responses = self.responses.get()
            response = None
            error = None
            if request:
                response = responses.get(request)
                error = errors.get(request)
            self.__update_editor_content(request, response, error)
        else:
            self.response.set_text("")

    def __update_editor_content(self, request: uuid.UUID | None, response: Response | None, error: BaseException | None):
        if request is not None:
            if error is not None:
                self.response.set_text(f"Request Failed: {str(error)}")
            elif response is not None:
                self.response.set_text(response.data.decode('utf-8'))
            else:
                self.response.set_text("")
        else:
            self.response.set_text("")

