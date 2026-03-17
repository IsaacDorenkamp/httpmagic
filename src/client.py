import httpx

from entities.request import Request


class MagicClient:
    _client: httpx.AsyncClient

    def __init__(self):
        self._client = httpx.AsyncClient(timeout=None)

    async def send(self, request: Request):
        return await self._client.request(
            method=request.method,
            url=request.url,
        )

