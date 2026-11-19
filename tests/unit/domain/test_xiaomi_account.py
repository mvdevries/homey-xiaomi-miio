from app.domain.xiaomi_account import (
    CloudDevice,
    QrChallenge,
    device_from_cloud,
    keep_supported,
    unique_by_id,
)


def make_device(did="1", model="zhimi.fan.za4", name="Fan", token="aa" * 16):
    return CloudDevice(did, name, model, token, "192.0.2.10", "de")


class TestQrChallenge:
    def test_given_an_image_when_asked_for_a_data_uri_then_it_is_base64(self):
        challenge = QrChallenge(b"abc", "login", "poll", 60, "image/png")

        assert challenge.image_data_uri == "data:image/png;base64,YWJj"


class TestCloudDevice:
    def test_given_a_device_when_converted_then_all_fields_are_listed(self):
        assert make_device().to_dict() == {
            "did": "1",
            "name": "Fan",
            "model": "zhimi.fan.za4",
            "token": "aa" * 16,
            "address": "192.0.2.10",
            "server": "de",
        }


class TestDeviceFromCloud:
    def test_given_a_cloud_entry_when_converted_then_a_device_is_made(self):
        info = {
            "did": 5,
            "name": "Fan",
            "model": "zhimi.fan.za4",
            "token": "aa" * 16,
            "localip": "192.0.2.10",
        }

        device = device_from_cloud(info, "de")

        assert device == CloudDevice(
            "5", "Fan", "zhimi.fan.za4", "aa" * 16, "192.0.2.10", "de"
        )

    def test_given_an_entry_without_token_when_converted_then_it_is_skipped(self):
        assert device_from_cloud({"model": "zhimi.fan.za4"}, "de") is None

    def test_given_an_entry_without_model_when_converted_then_it_is_skipped(self):
        assert device_from_cloud({"token": "aa" * 16}, "de") is None

    def test_given_an_entry_without_address_when_converted_then_it_is_empty(self):
        device = device_from_cloud({"token": "aa" * 16, "model": "m"}, "de")

        assert device.address == ""


class TestKeepSupported:
    def test_given_models_when_filtered_then_only_those_models_stay(self):
        devices = [make_device("1"), make_device("2", model="other.model.x1")]

        kept = keep_supported(devices, ("zhimi.fan.za4",))

        assert [device.did for device in kept] == ["1"]

    def test_given_no_models_when_filtered_then_everything_stays(self):
        devices = [make_device("1"), make_device("2", model="other.model.x1")]

        assert len(keep_supported(devices, ())) == 2


class TestUniqueById:
    def test_given_a_device_on_two_servers_when_deduplicated_then_one_stays(self):
        devices = [make_device("1"), make_device("1"), make_device("2")]

        assert [device.did for device in unique_by_id(devices)] == ["1", "2"]
