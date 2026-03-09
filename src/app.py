import framed
from views.collection_view import CollectionView


class App(framed.App):
    collection_pane: CollectionView

    def __init__(self, stdscr):
        super().__init__(stdscr)
        self.__configure()

    def __configure(self):
        manager = self.multiplex()
        app_split, command_split = manager.split(2, direction=framed.Direction.vertical)
        collection_split, request_split, response_split = manager.split(3, path=app_split, direction=framed.Direction.horizontal)

        manager.set_proportions((), (1, 0))
        manager.set_proportions(app_split, (1, 2, 2))

        self.collection_pane = self.new_panel(CollectionView, split_path=collection_split)


"""
class App:
    __stdscr: curses.window

    __store: PersistStore

    __mode: Mode
    __running: bool

    # UI
    __collection_pane: CollectionPane
    __command: controls.LineEdit

    __request_pane: RequestView
    __response_pane: ResponseView

    __focus: controls.Control | None

    # Internal
    __executor: executor.RequestExecutor

    # Public
    context: AppContext

    def __init__(self, stdscr: curses.window, context: AppContext, store: PersistStore):
        self.__stdscr = stdscr
        self.__store = store
        self.__mode = Mode.control
        self.__running = True
        self.context = context

        bounds = stdscr.getmaxyx()

        stdscr.bkgd(colors.color_pair(
            colors.get_color("foreground"),
            colors.get_color("background"),
        ))
        stdscr.refresh()

        self.__collection_pane = CollectionPane(abs_pos=(0, 0), size=(bounds[0] - 2, 50), parent=stdscr)
        self.__collection_pane.requests.change = self._request_changed

        pane_width = (bounds[1] - 50) // 2
        self.__request_pane = RequestView(abs_pos=(0, self.__collection_pane.size[1]), size=(bounds[0] - 2, pane_width), parent=self)
        self.__request_pane.set_content_visible(False)
        self.__response_pane = ResponseView(abs_pos=(0, self.__collection_pane.size[1] + pane_width), size=(bounds[0] - 2, (bounds[1] - 50) - pane_width), parent=self)

        self.__status  = controls.Label(abs_pos=(bounds[0] - 2, 0), size=(1, bounds[1]))
        self.__status.background = colors.get_color("contrast")
        self.__status.foreground = colors.get_color("foreground")
        self.__command = controls.LineEdit(bounds[1], abs_pos=(bounds[0] - 1, 0))

        self.__focus = None
        self.__executor = executor.RequestExecutor()

        if self.context.collections:
            collection = self.context.collections[0]
            self.set_active_collection(collection)
            if collection.requests:
                self.set_active_request(collection.requests[0])

        self.repaint()

    def relayout(self):
        bounds = self.__stdscr.getmaxyx()
        if bounds[1] <= 150:
            collection_width = 25
        else:
            collection_width = 50

        self.__collection_pane.set_size((bounds[0] - 2, collection_width))

        pane_width = (bounds[1] - collection_width) // 2
        with self.__request_pane.rearrange():
            self.__request_pane.set_absolute_pos((0, collection_width), repaint=False)
            self.__request_pane.set_size((bounds[0] - 2, pane_width))

        with self.__response_pane.rearrange():
            self.__response_pane.set_absolute_pos((0, collection_width + pane_width), repaint=False)
            self.__response_pane.set_size((bounds[0] - 2, 20))

        with self.__command.rearrange():
            self.__command.set_size((1, bounds[1] - 1))
            self.__command.set_absolute_pos((bounds[0] - 1, 0))

        with self.__status.rearrange():
            self.__status.set_size((1, bounds[1] - 1))
            self.__status.set_absolute_pos((bounds[0] - 2, 0))

        self.repaint()

    def repaint(self):
        self.__stdscr.erase()
        self.__stdscr.refresh()
        self.__collection_pane.repaint()
        self.__request_pane.repaint()
        self.__response_pane.repaint()
        self.__status.repaint()
        self.__command.repaint()

    def update_focus(self):
        if self.__focus is not None and not self.__focus.focused:
            self.__focus = None

    def set_focus(self, focus: controls.Control | None):
        if self.__focus is not None:
            self.__focus.unfocus()

        if focus:
            try:
                focus.focus()
                self.__focus = focus
            except controls.CannotFocus:
                self.__focus = None

    def update(self):
        for request_id, result in self.__executor.collect():
            if isinstance(result, httpx.Response):
                self.set_response(request_id, Response(status=result.status_code, headers=dict(result.headers), data=result.content))

    def run(self) -> int:
        curses.curs_set(0)
        self.__stdscr.nodelay(True)
        while self.__running:
            ch = self.__stdscr.getch()
            if ch == 27:
                next = self.__stdscr.getch()
                if next != -1:
                    continue
            elif ch == -1:
                self.update_focus()
                self.update()
                continue
            elif ch == curses.KEY_RESIZE:
                self.relayout()
                continue

            if self.__mode == Mode.control:
                can_take_focus = self.__focus is None or (self.__focus is not None and not self.__focus.focus_greedy)
                if ch == ord(':') and can_take_focus:
                    self.begin_command()
                elif ch == ord('T'):
                    self.set_focus(self.__response_pane.tabs)
                elif self.__focus is not None:
                    self.__focus.handle_input(ch)
                elif ch == controls.Control.CTRL_S:
                    self.set_focus(self.__collection_pane.requests)
                else:
                    self.__request_pane.handle_input(ch)
            else:
                if ch == ord('\n'):
                    self.execute_command()
                elif ch == 27:
                    self.cancel_command()
                else:
                    curses.curs_set(2)
                    self.update_command(ch)
                    command = self.__command.get_text()
                    if not command.startswith(':'):
                        self.cancel_command()

            self.update()

        return 0

    def begin_command(self):
        self.__mode = Mode.command
        self.__command.set_text(":")
        self.__command.focus()
        curses.curs_set(2)

    def cancel_command(self):
        curses.curs_set(0)
        self.__mode = Mode.control
        self.__command.set_text("")
        self.__command.unfocus()

    def execute_command(self):
        curses.curs_set(0)
        self.__mode = Mode.control
        command = self.__command.get_text()
        self.__command.set_text("")
        self.__command.unfocus()
        try:
            commands.execute(command, self)
            self.status_clear()
        except commands.CommandError as err:
            self.status_error("Error: " + str(err))

    def update_command(self, ch: int):
        self.__command.handle_input(ch)

    # convenience status functions
    def status_error(self, message: str):
        self.__status.set_text(message)
        self.__status.bold = True
        self.__status.italic = True
        self.__status.foreground = colors.get_color("error")
        self.__status.repaint()

    def status_info(self, message: str):
        self.__status.set_text(message)
        self.__status.bold = False
        self.__status.italic = False
        self.__status.foreground = colors.get_color("foreground")
        self.__status.repaint()

    def status_clear(self):
        self.__status.bold = False
        self.__status.italic = False
        self.__status.underline = False
        self.__status.set_text("")
        self.__status.repaint()

    # public API
    def set_response(self, request_key: uuid.UUID, response: Response):
        self.context.responses[request_key] = response
        if self.context.active_request and request_key == self.context.active_request.id:
            self.__response_pane.set_response(response)
            self.__response_pane.set_loading(False)

    def create_collection(self, name: str, activate: bool = False) -> Collection:
        new_collection_id = uuid.uuid4()
        # TODO: validate uniqueness of id
        new_collection = Collection(id=new_collection_id, requests=[], name=name)
        self.store.save_collection(new_collection)
        self.context.collections.append(new_collection)
        if activate:
            self.set_active_collection(new_collection)
        return new_collection

    def save_active_request(self):
        if self.context.active_collection and self.context.active_request:
            try:
                self.context.dirty.remove(self.context.active_request.id)
            except KeyError:
                raise ValueError("Request is up to date.")
            self.store.save_request(self.store.get_collection_root(self.context.active_collection), self.context.active_request)
            self.__request_pane.set_dirty(False)
        else:
            raise ValueError("There must be an active request to save.")

    def set_active_collection(self, collection: Collection):
        self.context.active_collection = collection
        self.__collection_pane.set_name(collection.name)
        self.__collection_pane.set_requests(request.name for request in collection.requests)

    def set_active_request(self, request: Request):
        if not self.context.active_collection:
            raise ValueError("There must be an active collection to set the active request.")

        self.context.active_request = request
        self.__request_pane.set_request_name(f"{self.context.active_collection.name} - {request.name}", dirty=request.id in self.context.dirty)
        self.__request_pane.set_method(request.method)
        self.__request_pane.set_url(request.url)
        self.__request_pane.set_content_visible(True)

        status = self.__executor.get_status(request.id)
        self.__response_pane.set_loading(status == executor.RequestStatus.pending)
        self.__response_pane.set_response(self.context.responses.get(request.id))

        self.__collection_pane.set_selected_request(request.name)

    def create_request(self, name: str, activate: bool = False) -> Request:
        if self.context.active_collection is None:
            raise ValueError("No active collection.")

        if name in [request.name for request in self.context.active_collection.requests]:
            raise ValueError("Request '%s' already exists in this collection." % name)

        new_id = uuid.uuid4()
        while new_id in {request.id for request in self.context.active_collection.requests}:
            new_id = uuid.uuid4()
        new_request = Request(id=new_id, name=name, method="GET", url="http://httpbin.org/get", headers={})
        self.store.save_request(self.store.get_collection_root(self.context.active_collection), new_request)
        self.context.active_collection.requests.append(new_request)
        self.__collection_pane.requests.insort_item(name, key=str.lower, select=True)
        if activate:
            self.set_active_request(new_request)
        return new_request

    def rename_active_request(self, name: str):
        if self.context.active_request is None or self.context.active_collection is None:
            raise ValueError("Not active request.")
        elif self.context.active_request.name == name:
            raise ValueError("Name was not changed!")

        existing = next((request for request in self.context.active_collection.requests if request.name == name), None)
        if existing is not None:
            raise ValueError("A request named '%s' already exists in this collection." % name)

        requests = self.__collection_pane.requests
        index = requests.find(self.context.active_request.name)
        if index >= 0:
            requests.set_item(index, name, resort=str.lower)
            new_index = requests.find(name)
            self.context.active_request.name = name
            requests.set_selection(new_index)
            self.__request_pane.set_request_name(f"{self.context.active_collection.name} - {self.context.active_request.name}")
        else:
            raise ValueError("Request '%s' does not exist in the current collection." % self.context.active_request.name)

    def rename_active_collection(self, name: str):
        if self.context.active_collection is None:
            raise ValueError("No collection is active.")
        elif name == self.context.active_collection.name:
            raise ValueError("Name was not changed!")

        existing = next((collection for collection in self.context.collections if collection.name == name), None)
        if existing is not None:
            raise ValueError("A collection named '%s' already exists." % name)

        self.context.active_collection.name = name
        self.__collection_pane.set_name(name)

    def execute_request(self):
        if self.context.active_request:
            self.__response_pane.set_loading(True)
            self.__executor.dispatch(self.context.active_request, self.context.active_request.id)

    def quit(self):
        self.__running = False

    # change listeners
    def _request_changed(self, request_name: str | None):
        if self.context.active_collection is None:
            return

        if request_name is None:
            self.__request_pane.set_content_visible(False)
        else:
            request = next((request for request in self.context.active_collection.requests if request.name == request_name), None)
            if request is not None:
                self.set_active_request(request)

    # properties
    @property
    def stdscr(self) -> curses.window:
        return self.__stdscr

    @property
    def store(self) -> PersistStore:
        return self.__store
"""

