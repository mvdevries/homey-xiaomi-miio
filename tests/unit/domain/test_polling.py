import pytest
from app.domain.polling import (
    DEFAULT_POLLING_SECONDS,
    MIN_POLLING_SECONDS,
    polling_seconds,
)


class TestPollingSeconds:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (None, DEFAULT_POLLING_SECONDS),
            (0, DEFAULT_POLLING_SECONDS),
            (1, MIN_POLLING_SECONDS),
            ("30", 30),
            (60, 60),
        ],
    )
    def test_given_a_polling_value_when_resolved_then_the_effective_seconds_return(
        self, value, expected
    ):
        seconds = polling_seconds(value)

        assert seconds == expected
