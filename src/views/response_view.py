from __future__ import annotations
import uuid

import framed
import framed.context
from framed.widgets import *
from framed import keys

from entities.response import Response
import util


class ResponseView(framed.Panel):
    active_request: framed.context.ContextRef[uuid.UUID | None]
    errors: framed.context.ContextRef[dict[uuid.UUID, BaseException]]
    responses: framed.context.ContextRef[dict[uuid.UUID, Response]]

    prestatus: Label
    status: Label
    time: Label
    content_size: Label
    response: Editor

    def __init__(self, region: framed.rect2, owner: framed.Manager, root: framed.App):
        super().__init__(region, owner, root)
        self.active_request = root.context.ref("active_request")
        self.errors = root.context.ref("errors")
        self.responses = root.context.ref("responses")

        self.active_request.handle(self.on_request_changed)
        self.errors.handle(self.on_errors_changed)
        self.responses.handle(self.on_responses_changed)

        self.prestatus = Label("")
        self.prestatus.foreground = "green"
        self.status = Label("")
        self.status.background = "green"
        self.time = Label("")
        self.content_size = Label("")
        self.response = Editor()
        self.response.editable = False
        self.response.bind(keys.j, EditorAction.nav_down)
        self.response.bind(keys.k, EditorAction.nav_up)
        self.response.bind(keys.h, EditorAction.nav_left)
        self.response.bind(keys.l, EditorAction.nav_right)
        self.response.bind(keys.ESCAPE, EditorAction.nav_unfocus)
        self.add(self.prestatus)
        self.add(self.status)
        self.add(self.time)
        self.add(self.content_size)
        self.add(self.response)

    def arrange(self):
        flex = self.flex()
        flex.set_row_weight(1, 1)
        flex.add_spacer(0, 1)
        flex.add(self.prestatus, 0, 0)
        flex.add(self.status, 0, 0)
        flex.add(self.time, 0, 0)
        flex.add(self.content_size, 0, 0)
        flex.add(self.response, 1, 1)

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
                self._clear()
                self.response.set_text(f"Request Failed: {str(error)}")
            elif response is not None:
                color = util.get_status_color(response.status)
                self.prestatus.set_text("\uE0B2")
                self.prestatus.foreground = color
                self.status.background = color
                self.status.set_text(f" {response.status} {util.get_status_phrase(response.status)} ")
                self.response.set_text(response.data.decode('utf-8'))
                self.content_size.set_text(f" {util.get_size_string(response.size)}")
                self.time.set_text(f" {response.time}ms")
                self.repaint()
            else:
                self._clear()
        else:
            self._clear()

    def _clear(self):
        self.prestatus.set_text("")
        self.status.set_text("")
        self.content_size.set_text("")
        self.time.set_text("")
        self.response.set_text("")
        self.repaint()

