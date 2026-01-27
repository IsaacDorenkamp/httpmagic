from controls import Control


class BinaryResponseView(Control):
    _content: bytes

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set_content(self, content: bytes):
        self._content = content

    def render(self):
        pass

    def handle_input(self, ch: int):
        pass


