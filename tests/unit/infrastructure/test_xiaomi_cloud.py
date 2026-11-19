import pytest
from app.domain.errors import (
    CloudRequestError,
    LoginExpiredError,
    LoginFailedError,
)
from app.infrastructure.http import HttpResponse
from app.infrastructure.xiaomi_cloud import (
    XiaomiCloudClient,
    api_url,
    parse_json,
)

from tests.support.fake_xiaomi_cloud import (
    LOCATION_URL,
    POLLING_URL,
    QR_IMAGE,
    FakeXiaomiCloud,
)

TOKEN = "00112233445566778899aabbccddeeff"


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


class TickingCloud(FakeXiaomiCloud):
    def __init__(self, clock):
        super().__init__()
        self._clock = clock

    async def _poll(self):
        self._clock.advance(100)
        return await super()._poll()


async def no_sleep(seconds):
    return None


def make_client(cloud, clock=None):
    return XiaomiCloudClient(cloud, clock=clock or FakeClock(), sleep=no_sleep)


class TestParseJson:
    def test_given_a_wrapped_answer_when_parsed_then_the_marker_is_removed(self):
        assert parse_json('&&&START&&&{"a": 1}') == {"a": 1}

    def test_given_text_that_is_not_json_when_parsed_then_it_fails(self):
        with pytest.raises(CloudRequestError):
            parse_json("<html>")


class TestApiUrl:
    def test_given_the_china_server_when_built_then_there_is_no_prefix(self):
        assert api_url("cn", "/x") == "https://api.io.mi.com/app/x"

    def test_given_another_server_when_built_then_it_is_the_prefix(self):
        assert api_url("de", "/x") == "https://de.api.io.mi.com/app/x"


class TestRequestQr:
    async def test_given_the_cloud_when_a_qr_is_requested_then_a_challenge_is_returned(
        self,
    ):
        challenge = await make_client(FakeXiaomiCloud()).request_qr()

        assert challenge.image == QR_IMAGE
        assert challenge.polling_url == POLLING_URL
        assert challenge.timeout_seconds == 300
        assert challenge.image_type == "image/png"

    async def test_given_a_cloud_error_when_a_qr_is_requested_then_it_fails(self):
        cloud = FakeXiaomiCloud()
        cloud.login_status = 500

        with pytest.raises(CloudRequestError):
            await make_client(cloud).request_qr()

    async def test_given_an_answer_without_qr_when_requested_then_it_fails(self):
        cloud = FakeXiaomiCloud()

        async def request(method, url, **options):

            return HttpResponse(200, b"&&&START&&&{}")

        cloud.request = request

        with pytest.raises(CloudRequestError):
            await make_client(cloud).request_qr()

    async def test_given_a_failing_image_when_requested_then_it_fails(self):
        cloud = FakeXiaomiCloud()
        original = cloud.request

        async def request(method, url, **options):

            if url.endswith(".png"):
                return HttpResponse(404, b"")
            return await original(method, url, **options)

        cloud.request = request

        with pytest.raises(CloudRequestError):
            await make_client(cloud).request_qr()


class TestWaitForScan:
    async def test_given_a_scanned_code_when_waited_then_the_session_lists_devices(
        self,
    ):
        cloud = FakeXiaomiCloud()
        cloud.scanned = True
        cloud.add_device(
            "de",
            did="7",
            name="Fan",
            model="zhimi.fan.za4",
            token=TOKEN,
            localip="192.0.2.10",
        )
        client = make_client(cloud)
        challenge = await client.request_qr()

        session = await client.wait_for_scan(challenge)
        devices = await session.list_devices("de")

        assert [(d.did, d.name, d.token, d.address) for d in devices] == [
            ("7", "Fan", TOKEN, "192.0.2.10")
        ]

    async def test_given_a_code_that_is_never_scanned_when_waited_then_it_expires(
        self,
    ):
        clock = FakeClock()
        cloud = TickingCloud(clock)
        client = make_client(cloud, clock)
        challenge = await client.request_qr()

        with pytest.raises(LoginExpiredError):
            await client.wait_for_scan(challenge)

    async def test_given_a_failing_poll_when_waited_then_it_retries_until_it_expires(
        self,
    ):
        clock = FakeClock()
        cloud = FakeXiaomiCloud()
        cloud.polling_status = 500
        client = make_client(cloud, clock)
        challenge = await client.request_qr()

        async def sleep(seconds):
            clock.advance(seconds * 100)

        client._sleep = sleep

        with pytest.raises(LoginExpiredError):
            await client.wait_for_scan(challenge)

    async def test_given_an_incomplete_answer_when_waited_then_the_login_fails(self):
        cloud = FakeXiaomiCloud()
        cloud.scanned = True

        async def poll():

            return HttpResponse(200, b'&&&START&&&{"userId": 1}')

        cloud._poll = poll
        client = make_client(cloud)
        challenge = await client.request_qr()

        with pytest.raises(LoginFailedError):
            await client.wait_for_scan(challenge)

    async def test_given_no_service_token_when_waited_then_the_login_fails(self):
        cloud = FakeXiaomiCloud()
        cloud.scanned = True
        original = cloud.request

        async def request(method, url, **options):

            if url == LOCATION_URL:
                return HttpResponse(200, b"ok")
            return await original(method, url, **options)

        cloud.request = request
        client = make_client(cloud)
        challenge = await client.request_qr()

        with pytest.raises(LoginFailedError):
            await client.wait_for_scan(challenge)


class TestCloudSession:
    async def make_session(self, cloud):
        cloud.scanned = True
        client = make_client(cloud)
        return await client.wait_for_scan(await client.request_qr())

    async def test_given_shared_homes_when_listed_then_their_devices_are_included(
        self,
    ):
        cloud = FakeXiaomiCloud()
        cloud.shared_homes["de"] = [{"home_id": 9, "home_owner": 22}]
        cloud.devices["de"] = [
            {"did": "1", "model": "zhimi.fan.za4", "token": TOKEN, "name": "Fan"}
        ]
        session = await self.make_session(cloud)

        devices = await session.list_devices("de")

        assert len(devices) == 1

    async def test_given_a_server_without_homes_when_listed_then_nothing_is_found(
        self,
    ):
        session = await self.make_session(FakeXiaomiCloud())

        assert await session.list_devices("us") == []

    async def test_given_a_device_without_token_when_listed_then_it_is_skipped(self):
        cloud = FakeXiaomiCloud()
        cloud.add_device("de", did="1", model="zhimi.fan.za4", name="Fan")
        session = await self.make_session(cloud)

        assert await session.list_devices("de") == []

    async def test_given_a_cloud_error_when_listed_then_the_request_fails(self):
        cloud = FakeXiaomiCloud()
        session = await self.make_session(cloud)
        cloud.broken_servers.add("de")

        with pytest.raises(CloudRequestError):
            await session.list_devices("de")
