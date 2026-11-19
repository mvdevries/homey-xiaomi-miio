from app.domain.discovery import DiscoveredDevice, short_hostname


class TestDiscoveredDevice:
    def test_given_a_device_when_converted_then_the_id_is_hexadecimal(self):
        device = DiscoveredDevice("192.0.2.10", 0x1234)

        assert device.to_dict() == {
            "address": "192.0.2.10",
            "deviceId": "00001234",
            "name": "",
            "model": "",
            "productName": "",
        }

    def test_given_a_miio_hostname_when_asked_for_the_model_then_it_is_derived(self):
        device = DiscoveredDevice("192.0.2.10", 1, "zhimi-fan-za4_mibt0FE4")

        assert device.model == "zhimi.fan.za4"

    def test_given_another_hostname_when_asked_for_the_model_then_it_is_empty(self):
        device = DiscoveredDevice("192.0.2.10", 1, "living-room-tv")

        assert device.model == ""

    def test_given_a_supported_model_when_named_then_the_product_name_is_given(
        self,
    ):
        device = DiscoveredDevice("192.0.2.10", 1, "zhimi-fan-za4_mibt0FE4")

        assert device.product_name == "Mi Smart Standing Fan"

    def test_given_an_unknown_model_when_named_then_the_product_name_is_empty(
        self,
    ):
        device = DiscoveredDevice("192.0.2.10", 1, "acme-gadget-x1_mibt1")

        assert device.product_name == ""


class TestShortHostname:
    def test_given_a_fully_qualified_name_when_shortened_then_the_domain_is_dropped(
        self,
    ):
        assert short_hostname("lamp_mibt1.home.example") == "lamp_mibt1"
