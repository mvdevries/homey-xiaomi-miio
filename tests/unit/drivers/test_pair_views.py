from pathlib import Path

import pytest

DRIVERS_DIRECTORY = Path(__file__).resolve().parents[3] / "drivers"
PAIR_VIEWS = sorted(DRIVERS_DIRECTORY.glob("*/pair/pair.html"))


class TestPairView:
    def test_given_the_drivers_when_listed_then_each_has_a_pair_view(self):
        assert len(PAIR_VIEWS) == len(list(DRIVERS_DIRECTORY.iterdir()))

    @pytest.mark.parametrize("view", PAIR_VIEWS, ids=lambda view: view.parts[-3])
    def test_given_a_pair_view_when_compared_then_it_matches_the_first_one(self, view):
        first = PAIR_VIEWS[0].read_text()

        assert view.read_text() == first
