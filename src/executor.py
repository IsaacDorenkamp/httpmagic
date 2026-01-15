import threading
import queue
import typing

import httpx

from entities.request import Request


class RequestThread(threading.Thread):
    _request: Request
    _id: str
    _target: queue.Queue[tuple[str, httpx.Response | Exception]]

    def __init__(self, request: Request, exec_id: str, target: queue.Queue[tuple[str, httpx.Response | Exception]]):
        self._request = request
        self._id = exec_id
        self._target = target

    def run(self):
        try:
            result = httpx.request(
                method=self._request.method,
                url=self._request.url
            )
            self._target.put((self._id, result))
        except Exception as err:
            self._target.put((self._id, err))


class RequestExecutor:
    _should_exit: threading.Event
    _responses: queue.Queue

    def __init__(self):
        super().__init__()
        self._should_exit = threading.Event()
        self._responses = queue.Queue()

    def dispatch(self, request: Request, id: str):
        thread = RequestThread(request.copy(), id, self._responses)
        thread.run()

    def collect(self) -> typing.Generator[tuple[str, httpx.Response | Exception], None, None]:
        while not self._responses.empty():
            yield self._responses.get()

