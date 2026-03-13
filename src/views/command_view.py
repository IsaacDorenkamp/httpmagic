from __future__ import annotations
import logging
import typing

import framed
import framed.event
from framed import keys
from framed.widgets import *
from framed import Panel

import commands


class CommandView(Panel):
    status: Label
    command: Editor

    def __init__(self, region: framed.rect2, owner: framed.Manager, root: framed.App):
        super().__init__(region, owner, root)
        self.status = Label("")
        self.command = Editor()
        self.command.unbind(keys.ESCAPE)
        self.command.bind(keys.ENTER, EditorAction.edit_finish)
        self.command.listen(framed.event.ChangeEvent, self.on_command)
        self.add(self.status)
        self.add(self.command)

    def arrange(self):
        grid = self.grid()
        grid.add(self.status, 0, 0)
        grid.add(self.command, 1, 0)

    def on_command(self, event: framed.event.ChangeEvent[str]):
        from app import App
        self.command.set_text("")
        try:
            commands.execute(event.value, typing.cast(App, self.root))
            self.__info("")
        except commands.CommandError as err:
            self.__error(str(err))
        except Exception:
            logging.exception(f"An error occured when executing a command: {event.value}")
            self.__error("An unexpected error occurred.")

    def __error(self, err: str):
        self.status.foreground = "red"
        self.status.bold = True
        self.status.italic = True
        self.status.set_text(err)

    def __info(self, info: str):
        self.status.foreground = "default"
        self.status.bold = False
        self.status.italic = False
        self.status.set_text(info)

