from pathlib import Path

import pytest

DRIVERS_DIRECTORY = Path(__file__).resolve().parents[3] / "drivers"
VIEW_NAMES = ("start", "discover", "pair")
PAIR_VIEWS = sorted(DRIVERS_DIRECTORY.glob("*/pair/*.html"))


class TestPairView:
    def test_given_the_drivers_when_listed_then_each_has_every_pair_view(self):
        drivers = len(list(DRIVERS_DIRECTORY.iterdir()))

        assert len(PAIR_VIEWS) == drivers * len(VIEW_NAMES)

    @pytest.mark.parametrize("name", VIEW_NAMES)
    def test_given_a_pair_view_when_compared_then_every_driver_has_the_same_copy(
        self, name
    ):
        copies = {
            view.read_text() for view in PAIR_VIEWS if view.name == f"{name}.html"
        }

        assert len(copies) == 1
