import asyncio
import urllib.error
import urllib.request
from dataclasses import dataclass
from http.cookiejar import CookieJar
from urllib.parse import urlencode

from ..domain.errors import CloudRequestError, CloudTimeoutError

DEFAULT_TIMEOUT_SECONDS = 10.0
START_MARKER = "&&&START&&&"


@dataclass(frozen=True, slots=True)
class HttpResponse:
    status: int
    body: bytes
    content_type: str = ""

    @property
    def text(self) -> str:
        return self.body.decode(errors="replace")


class HttpClient:
    def __init__(self) -> None:
        self._cookies = CookieJar()
        self._opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self._cookies)
        )

    def cookie(self, name: str) -> str | None:
        for cookie in self._cookies:
            if cookie.name == name:
                return cookie.value
        return None

    async def request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> HttpResponse:
        return await asyncio.to_thread(
            self._request,
            method,
            url,
            params,
            headers or {},
            cookies or {},
            timeout_seconds,
        )

    def _request(
        self,
        method: str,
        url: str,
        params: dict[str, str] | None,
        headers: dict[str, str],
        cookies: dict[str, str],
        timeout: float,
    ) -> HttpResponse:
        if params:
            url = f"{url}?{urlencode(params)}"
        request = urllib.request.Request(
            url, data=b"" if method == "POST" else None, method=method
        )
        for name, value in headers.items():
            request.add_header(name, value)
        if cookies:
            request.add_header(
                "Cookie", "; ".join(f"{key}={value}" for key, value in cookies.items())
            )
        try:
            with self._opener.open(request, timeout=timeout) as response:
                return self._response(response.status, response)
        except urllib.error.HTTPError as error:
            return self._response(error.code, error)
        except TimeoutError as error:
            raise CloudTimeoutError(str(error)) from error
        except (urllib.error.URLError, OSError) as error:
            if isinstance(error, urllib.error.URLError) and isinstance(
                error.reason, TimeoutError
            ):
                raise CloudTimeoutError(str(error)) from error
            raise CloudRequestError(str(error)) from error

    @staticmethod
    def _response(status: int, response) -> HttpResponse:
        return HttpResponse(
            status, response.read(), response.headers.get("Content-Type", "")
        )
