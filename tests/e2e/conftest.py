from collections.abc import Iterator

import pytest

from tests.e2e.backend import Backend


@pytest.fixture
def backend(monkeypatch) -> Iterator[Backend]:
    running_backend = Backend(monkeypatch)
    running_backend.start()
    yield running_backend
    running_backend.stop()


@pytest.fixture
def pairing_page(page, backend):
    def open_page(driver_id: str, language: str = "en", view: str = "pair"):
        page.goto(
            f"{backend.base_url}/pair.html"
            f"?driver={driver_id}&lang={language}&view={view}"
        )
        return page

    return open_page
