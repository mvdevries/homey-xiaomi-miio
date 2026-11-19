from app.domain.discovery import DiscoveredDevice


class TestDiscoveredDevice:
    def test_given_a_device_when_converted_then_the_id_is_hexadecimal(self):
        device = DiscoveredDevice("192.0.2.10", 0x1234)

        assert device.to_dict() == {"address": "192.0.2.10", "deviceId": "00001234"}
