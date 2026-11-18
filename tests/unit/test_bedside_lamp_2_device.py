from tests.support import load_module

device_module = load_module("drivers.yeelink-light-bslamp2.device")


async def test_device_is_unavailable_until_the_connection_exists():
    messages = []

    class Recorder(device_module.BedsideLamp2Device):
        async def set_unavailable(self, message=None):
            messages.append(message)

    await Recorder().on_init()

    assert messages == ["The miIO connection is not implemented yet"]
