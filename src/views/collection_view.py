import typing

from controls import Label, ListBox, Panel
from controls.layout import LineFlexData, LineFlexLayout


class CollectionPane(Panel):
    __name: Label
    __requests: ListBox

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__name = Label(parent=self._win)
        self.__name.bold = True
        self.__name.italic = True
        self.__name.underline = True
        self.__name.fill = True

        self.__requests = ListBox(parent=self._win)

        self.add(self.__name)
        self.add(self.__requests)

        layout = LineFlexLayout()
        layout.add_child(self.__name, LineFlexData(line=0, order=0, stretch=True))
        layout.add_child(self.__requests, LineFlexData(line=1, order=0, stretch=True))
        layout.set_line_weight(1, 1)
        self.set_layout(layout)

    def set_name(self, name: str):
        self.__name.set_text(name)

    def set_requests(self, requests: typing.Iterable[str]):
        self.__requests.clear()
        for request in sorted(requests):
            self.__requests.add_item(request)

    def set_selected_request(self, request: str):
        self.__requests.set_selection(self.__requests.find(request))

    @property
    def requests(self) -> ListBox:
        return self.__requests

