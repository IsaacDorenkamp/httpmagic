from abc import ABCMeta, abstractmethod


class CannotFocus(NotImplementedError):
    pass


class Control(metaclass=ABCMeta):
    __focused: bool
    def __init__(self):
        self.__focused = False

    def try_focus(self):
        """
        Try to accept focus. If this component
        cannot accept focus, this function
        should raise CannotFocus.
        """
        pass

    def focus(self):
        """
        Attempt to grant focus to this control.
        If the control cannot accept focus, then
        this function should raise CannotFocus.
        """
        if not self.__focused:
            try:
                self.try_focus()
                self.__focused = True
            except CannotFocus:
                pass

    def on_unfocus(self):
        """
        What to do before focus is revoked from
        this control.
        """
        pass

    def unfocus(self):
        """
        Attempt to revoke focus from this control.
        Defaults to doing nothing.
        """
        if self.__focused:
            self.on_unfocus()
            self.__focused = False

    @abstractmethod
    def handle_input(self, ch: int):
        raise NotImplementedError()

    @property
    def focused(self) -> bool:
        return self.__focused

