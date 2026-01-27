from .control import Control, Container


class SwitchPane(Container):
    _active: Control | None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._active = None

    def set_active(self, control: Control | None):
        if control is not None and control not in self._children:
            raise ValueError("control '%s' not in this pane!" % str(control))
        
        self._active = control
        if self._active:
            self._active.set_size(self.size)

        self.repaint()

    def add(self, control: Control):
        super().add(control)
        control.set_size(self.size)

    def set_size(self, size: tuple[int, int]) -> bool:
        result = super().set_size(size)
        return result

    def remove(self, control: Control):
        super().remove(control)
        if control == self._active:
            self._active = None
            self.repaint()

    def handle_input(self, ch: int):
        if self._active is not None:
            self._active.handle_input(ch)

