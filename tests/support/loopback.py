from collections.abc import Callable

from app.infrastructure.transport import MiioTransport

UNUSED_PORT = 9
TEST_TIMEOUT_SECONDS = 0.4
TEST_RETRIES = 1
TEST_POLLING_SECONDS = 0.05
LOOPBACK_ADDRESS = "127.0.0.1"


def build_transport_factory(
    ports: dict[str, int],
) -> Callable[[str, bytes], MiioTransport]:
    def create_test_transport(address: str, token: bytes) -> MiioTransport:
        return MiioTransport(
            LOOPBACK_ADDRESS,
            token,
            port=ports.get(address, UNUSED_PORT),
            timeout=TEST_TIMEOUT_SECONDS,
            retries=TEST_RETRIES,
        )

    return create_test_transport


def install_loopback_transport(monkeypatch, ports: dict[str, int]) -> None:
    monkeypatch.setattr(
        "app.container.create_transport", build_transport_factory(ports)
    )
    monkeypatch.setattr(
        "app.endpoints.polling_device.polling_seconds",
        lambda value: TEST_POLLING_SECONDS,
    )
