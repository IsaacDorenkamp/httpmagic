import enum
import queue
import threading
import typing
import uuid

import httpx

from entities.request import Request


class RequestStatus(enum.Enum):
    idle = 0
    pending = 1
    failed = 2   # failure doesn't indicate HTTP errors, only network errors
    success = 3


class RequestError(Exception):
    pass


class RequestThread(threading.Thread):
    _request: Request
    _id: uuid.UUID
    _target: queue.Queue[tuple[uuid.UUID, httpx.Response | Exception]]

    def __init__(self, request: Request, id: uuid.UUID, target: queue.Queue[tuple[uuid.UUID, httpx.Response | Exception]]):
        self._request = request
        self._id = id
        self._target = target

    def run(self):
        try:
            result = httpx.request(
                method=self._request.method,
                url=self._request.url,
                timeout=60,
            )
            self._target.put((self._id, result))
        except Exception as err:
            self._target.put((self._id, err))


class RequestExecutor:
    __responses: queue.Queue[tuple[uuid.UUID, httpx.Response | Exception]]
    __status: dict[uuid.UUID, RequestStatus]

    def __init__(self):
        super().__init__()
        self.__responses = queue.Queue()
        self.__status = {}

    def dispatch(self, request: Request, id: uuid.UUID):
        if self.__status.get(id, RequestStatus.idle) == RequestStatus.pending:
            raise RequestError("Request %s already in progress!" % str(id))

        self.__status[id] = RequestStatus.pending
        thread = RequestThread(request.copy(), id, self.__responses)
        thread.run()

    def collect(self) -> typing.Generator[tuple[uuid.UUID, httpx.Response | Exception], None, None]:
        while not self.__responses.empty():
            req_id, result = self.__responses.get()
            if isinstance(result, Exception):
                self.__status[req_id] = RequestStatus.failed
            else:
                self.__status[req_id] = RequestStatus.success
            yield req_id, result

    def get_status(self, request: uuid.UUID):
        return self.__status.get(request, RequestStatus.idle)

