import pytest
from app.domain.errors import MiioDeviceError


class TestMiioDeviceError:
    def test_given_a_code_and_message_when_created_then_the_message_names_both(self):
        error = MiioDeviceError(-1, "failure")

        assert str(error) == "miIO error -1: failure"
        assert error.code == -1

    @pytest.mark.parametrize("code", [-30001, -9999])
    def test_given_a_recoverable_code_when_checked_then_it_is_recoverable(self, code):
        error = MiioDeviceError(code, "retry")

        recoverable = error.recoverable

        assert recoverable is True

    @pytest.mark.parametrize("code", [-1, 0, -6011])
    def test_given_another_code_when_checked_then_it_is_not_recoverable(self, code):
        error = MiioDeviceError(code, "fatal")

        recoverable = error.recoverable

        assert recoverable is False
