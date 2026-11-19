import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from app.domain.errors import CloudRequestError, CloudTimeoutError
from app.infrastructure.http import HttpClient, HttpResponse


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        return

    def do_GET(self):
        self._answer_safely()

    def do_POST(self):
        self._answer_safely()

    def _answer_safely(self):
        try:
            self._answer()
        except BrokenPipeError, ConnectionResetError:
            return

    def _answer(self):
        if self.path.startswith("/slow"):
            time.sleep(0.5)
        status = 404 if self.path.startswith("/missing") else 200
        body = json.dumps(
            {
                "method": self.command,
                "path": self.path,
                "cookie": self.headers.get("Cookie"),
                "agent": self.headers.get("X-Test"),
            }
        ).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Set-Cookie", "serviceToken=abc; Path=/")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


@pytest.fixture
def server():
    running = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=running.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{running.server_address[1]}"
    running.shutdown()
    running.server_close()


class TestHttpResponse:
    def test_given_a_body_when_read_as_text_then_it_is_decoded(self):
        assert HttpResponse(200, "héllo".encode()).text == "héllo"


class TestHttpClient:
    async def test_given_a_get_when_requested_then_params_headers_and_cookies_are_sent(
        self, server
    ):
        response = await HttpClient().request(
            "GET",
            server + "/path",
            params={"a": "1 2"},
            headers={"X-Test": "agent"},
            cookies={"userId": "5", "locale": "en"},
        )

        data = json.loads(response.text)
        assert response.status == 200
        assert response.content_type == "application/json"
        assert data["path"] == "/path?a=1+2"
        assert data["agent"] == "agent"
        assert data["cookie"] == "userId=5; locale=en"

    async def test_given_a_post_when_requested_then_the_method_is_post(self, server):
        response = await HttpClient().request("POST", server + "/path")

        assert json.loads(response.text)["method"] == "POST"

    async def test_given_a_cookie_from_the_server_when_asked_then_it_is_found(
        self, server
    ):
        client = HttpClient()

        await client.request("GET", server + "/path")

        assert client.cookie("serviceToken") == "abc"
        assert client.cookie("other") is None

    async def test_given_an_error_status_when_requested_then_it_is_returned(
        self, server
    ):
        response = await HttpClient().request("GET", server + "/missing")

        assert response.status == 404

    async def test_given_a_slow_server_when_requested_then_it_times_out(self, server):
        with pytest.raises(CloudTimeoutError):
            await HttpClient().request("GET", server + "/slow", timeout_seconds=0.1)

    async def test_given_no_server_when_requested_then_the_request_fails(self):
        with pytest.raises(CloudRequestError):
            await HttpClient().request("GET", "http://127.0.0.1:9/")
