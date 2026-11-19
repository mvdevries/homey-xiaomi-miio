import asyncio
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

from app.domain.discovery import DiscoveredDevice
from app.endpoints.pairing_driver import MiioDriver
from app.infrastructure.xiaomi_cloud import XiaomiCloudClient

from tests.support import load_module
from tests.support.fake_miio_devices import DEVICE_ADDRESS, FakeBedsideLamp
from tests.support.fake_xiaomi_cloud import FakeXiaomiCloud
from tests.support.loop_harness import LoopHarness
from tests.support.loopback import install_loopback_transport

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOCALES_DIRECTORY = PROJECT_ROOT / "locales"
DRIVERS_DIRECTORY = PROJECT_ROOT / "drivers"
EMIT_PREFIX = "/__emit/"
CREATE_DEVICE_PATH = "/__create_device"
HOMEY_STUB_PATH = "/homey.js"
PAIR_PATH = "/pair.html"
ACCOUNT_EVENTS = {
    "start_account_login": "start_account_login",
    "account_login_status": "account_login_status",
    "account_devices": "account_devices",
}

HOMEY_STUB_TEMPLATE = """
(function () {
  const locales = __LOCALES__;
  const language = new URLSearchParams(location.search).get("lang") || "en";
  function lookup(key) {
    return key.split(".").reduce(function (node, part) {
      return node === undefined ? undefined : node[part];
    }, locales[language]);
  }
  function translate(key) {
    const text = lookup(key);
    return text === undefined ? key : text;
  }
  async function post(path, body) {
    const response = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body || {}),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error);
    return payload;
  }
  window.Homey = {
    __: translate,
    setTitle: function (title) {
      document.title = title;
      window.pairTitle = title;
    },
    emit: function (event, data) {
      return post("__EMIT__" + event, data);
    },
    createDevice: function (device) {
      return post("__CREATE__", device);
    },
    showView: function (view) {
      const parameters = new URLSearchParams(location.search);
      parameters.set("view", view);
      location.search = parameters.toString();
      return Promise.resolve();
    },
    setViewStoreValue: function (view, key, value) {
      sessionStorage.setItem(view + "." + key, value);
      return Promise.resolve();
    },
    getViewStoreValue: function (view, key) {
      return Promise.resolve(sessionStorage.getItem(view + "." + key));
    },
    done: function () {
      window.pairDone = true;
    },
  };
})();
"""

PAGE_TEMPLATE = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <script src="__STUB__"></script>
  </head>
  <body>
__BODY__
  </body>
</html>
"""


def build_homey_stub() -> bytes:
    locales = {
        language: json.loads((LOCALES_DIRECTORY / f"{language}.json").read_text())
        for language in ("en", "nl")
    }
    script = HOMEY_STUB_TEMPLATE.replace("__LOCALES__", json.dumps(locales))
    script = script.replace("__EMIT__", EMIT_PREFIX).replace(
        "__CREATE__", CREATE_DEVICE_PATH
    )
    return script.encode()


def build_pair_page(driver_id: str, view: str) -> bytes:
    body = (DRIVERS_DIRECTORY / driver_id / "pair" / f"{view}.html").read_text()
    page = PAGE_TEMPLATE.replace("__STUB__", HOMEY_STUB_PATH).replace("__BODY__", body)
    return page.encode()


class FakeScanner:
    def __init__(self, devices: list[DiscoveredDevice], delay: float) -> None:
        self._devices = devices
        self._delay = delay

    async def scan(self) -> list[DiscoveredDevice]:
        await asyncio.sleep(self._delay)
        return self._devices


async def no_sleep(seconds: float) -> None:
    return None


class Backend:
    def __init__(self, monkeypatch) -> None:
        self._monkeypatch = monkeypatch
        self._harness = LoopHarness()
        self._server: ThreadingHTTPServer | None = None
        self.lamp = FakeBedsideLamp()
        self.created_devices: list[dict[str, Any]] = []
        self.discovered_devices: list[DiscoveredDevice] = []
        self.cloud = FakeXiaomiCloud()
        self.scan_delay_seconds = 0.0
        self._driver: MiioDriver | None = None
        self.base_url = ""

    def start(self) -> None:
        self._harness.start()
        self._harness.call(self.lamp.start())
        install_loopback_transport(self._monkeypatch, {DEVICE_ADDRESS: self.lamp.port})
        self._monkeypatch.setattr(
            "app.container.create_authenticator",
            lambda: XiaomiCloudClient(self.cloud, sleep=no_sleep),
        )
        self._harness.call(self._create_driver())
        self._monkeypatch.setattr(
            "app.container.create_scanner",
            lambda: FakeScanner(self.discovered_devices, self.scan_delay_seconds),
        )
        self._server = ThreadingHTTPServer(("127.0.0.1", 0), self._build_handler())
        self.base_url = f"http://127.0.0.1:{self._server.server_address[1]}"
        threading.Thread(target=self._server.serve_forever, daemon=True).start()

    async def _create_driver(self) -> None:
        module = load_module("drivers.yeelink-light-bslamp2.driver")
        self._driver = module.homey_export()

    def stop(self) -> None:
        self._harness.call(self._stop_waiting())
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
        self.lamp.stop()
        self._harness.stop()

    def validate_device(self, data: dict[str, Any]) -> dict[str, Any]:
        return self._harness.call(MiioDriver().validate_device(data))

    async def _stop_waiting(self) -> None:
        service = self._driver._account_login
        if service is not None:
            service.close()
            await asyncio.sleep(0)

    def call_driver(self, handler: str, data: dict[str, Any]) -> Any:
        return self._harness.call(getattr(self._driver, handler)(data))

    def discover_devices(self) -> list[dict[str, Any]]:
        return self._harness.call(MiioDriver().discover_devices())

    def _build_handler(self) -> type[BaseHTTPRequestHandler]:
        backend = self
        homey_stub = build_homey_stub()

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args: Any) -> None:
                return

            def do_GET(self) -> None:
                url = urlsplit(self.path)
                if url.path == HOMEY_STUB_PATH:
                    self._send(200, homey_stub, "application/javascript")
                elif url.path == PAIR_PATH:
                    query = parse_qs(url.query)
                    driver_id = query["driver"][0]
                    view = query.get("view", ["pair"])[0]
                    self._send(200, build_pair_page(driver_id, view), "text/html")
                else:
                    self._send(404, b"not found", "text/plain")

            def do_POST(self) -> None:
                path = urlsplit(self.path).path
                length = int(self.headers.get("Content-Length") or 0)
                body = json.loads(self.rfile.read(length) or b"{}")
                if path == EMIT_PREFIX + "validate_device":
                    self._validate(body)
                elif path == EMIT_PREFIX + "discover_devices":
                    self._send_json(200, backend.discover_devices())
                elif path.startswith(EMIT_PREFIX) and path[len(EMIT_PREFIX) :] in (
                    ACCOUNT_EVENTS
                ):
                    self._emit_to_driver(ACCOUNT_EVENTS[path[len(EMIT_PREFIX) :]], body)
                elif path == CREATE_DEVICE_PATH:
                    backend.created_devices.append(body)
                    self._send_json(200, {})
                else:
                    self._send_json(404, {"error": "unknown_route"})

            def _emit_to_driver(self, handler: str, body: dict[str, Any]) -> None:
                try:
                    result = backend.call_driver(handler, body)
                except Exception as error:
                    self._send_json(400, {"error": str(error)})
                else:
                    self._send_json(200, result)

            def _validate(self, body: dict[str, Any]) -> None:
                try:
                    device = backend.validate_device(body)
                except Exception as error:
                    self._send_json(400, {"error": str(error)})
                else:
                    self._send_json(200, device)

            def _send_json(self, status: int, payload: Any) -> None:
                self._send(status, json.dumps(payload).encode(), "application/json")

            def _send(self, status: int, content: bytes, content_type: str) -> None:
                self.send_response(status)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)

        return Handler
