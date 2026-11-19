import pytest
from app.application.connection_policy import (
    FAILURES_BEFORE_UNAVAILABLE,
    failure_limit,
    should_mark_unavailable,
)


class TestFailureLimit:
    def test_given_a_device_that_never_connected_when_limited_then_one_failure_counts(
        self,
    ):
        limit = failure_limit(False)

        assert limit == 1

    def test_given_a_connected_device_when_limited_then_a_few_failures_are_tolerated(
        self,
    ):
        limit = failure_limit(True)

        assert limit == FAILURES_BEFORE_UNAVAILABLE


class TestShouldMarkUnavailable:
    @pytest.mark.parametrize(
        ("failures", "connected", "expected"),
        [
            (0, False, False),
            (1, False, True),
            (2, True, False),
            (FAILURES_BEFORE_UNAVAILABLE, True, True),
        ],
    )
    def test_given_failures_and_connection_state_when_checked_then_the_limit_decides(
        self, failures, connected, expected
    ):
        result = should_mark_unavailable(failures, connected)

        assert result is expected
