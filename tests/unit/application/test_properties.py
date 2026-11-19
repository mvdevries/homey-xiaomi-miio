import pytest
from app.application.properties import read_properties
from app.domain.errors import MiioDeviceError

from tests.support.fake_transport import FakeTransport


class TestReadProperties:
    async def test_given_a_batch_capable_device_when_read_then_one_request_is_sent(
        self,
    ):
        transport = FakeTransport(properties={"power": "on", "mode": "auto"})

        values = await read_properties(transport, ["power", "mode"])

        assert values == {"power": "on", "mode": "auto"}
        assert transport.calls == [("get_prop", ["power", "mode"])]

    async def test_given_no_batch_support_when_read_then_it_asks_per_property(
        self,
    ):
        transport = FakeTransport(
            properties={"power": "on", "mode": "auto"}, supports_batch=False
        )

        values = await read_properties(transport, ["power", "mode"])

        assert values == {"power": "on", "mode": "auto"}
        assert transport.calls == [
            ("get_prop", ["power", "mode"]),
            ("get_prop", ["power"]),
            ("get_prop", ["mode"]),
        ]

    async def test_given_a_short_batch_result_when_read_then_it_falls_back(self):
        transport = FakeTransport(result=["on"])

        values = await read_properties(transport, ["power", "mode"])

        assert values == {"power": "on", "mode": "on"}

    async def test_given_no_values_when_read_then_the_properties_are_none(self):
        transport = FakeTransport(result=[], properties=None)

        values = await read_properties(transport, ["power"])

        assert values == {"power": None}

    async def test_given_a_failing_optional_property_when_read_then_it_is_none(self):
        transport = FakeTransport(properties={"power": "on"}, failing={"dry": -1})

        values = await read_properties(transport, ["power", "dry"], frozenset({"dry"}))

        assert values == {"power": "on", "dry": None}

    async def test_given_a_failing_required_property_when_read_then_the_error_is_raised(
        self,
    ):
        transport = FakeTransport(properties={"power": "on"}, failing={"power": -1})

        with pytest.raises(MiioDeviceError):
            await read_properties(transport, ["power"])
