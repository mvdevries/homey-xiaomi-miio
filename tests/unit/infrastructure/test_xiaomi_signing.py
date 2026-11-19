import base64

from app.infrastructure.xiaomi_signing import (
    decrypt_payload,
    encrypt_payload,
    encrypted_params,
    generate_nonce,
    signature,
    signed_nonce,
)

SSECURITY = base64.b64encode(bytes(range(16))).decode()
NONCE = base64.b64encode(bytes(range(12))).decode()
URL = "https://de.api.io.mi.com/app/v2/homeroom/gethome"


class TestGenerateNonce:
    def test_given_a_time_when_generated_then_it_is_twelve_bytes_ending_in_minutes(
        self,
    ):
        raw = base64.b64decode(generate_nonce(120_000))

        assert len(raw) == 12
        assert int.from_bytes(raw[8:], "big") == 2

    def test_given_two_calls_when_generated_then_the_nonces_differ(self):
        assert generate_nonce(0) != generate_nonce(0)


class TestSignedNonce:
    def test_given_the_same_input_when_signed_then_the_result_is_stable(self):
        assert signed_nonce(SSECURITY, NONCE) == signed_nonce(SSECURITY, NONCE)

    def test_given_another_nonce_when_signed_then_the_result_differs(self):
        other = base64.b64encode(bytes(range(1, 13))).decode()

        assert signed_nonce(SSECURITY, NONCE) != signed_nonce(SSECURITY, other)


class TestPayloadEncryption:
    def test_given_a_payload_when_encrypted_and_decrypted_then_it_is_restored(self):
        signed = signed_nonce(SSECURITY, NONCE)

        encrypted = encrypt_payload(signed, '{"a": 1}')

        assert encrypted != '{"a": 1}'
        assert decrypt_payload(signed, encrypted) == '{"a": 1}'


class TestSignature:
    def test_given_params_when_signed_then_the_path_drops_the_app_prefix(self):
        signed = signed_nonce(SSECURITY, NONCE)

        with_prefix = signature("post", URL, {"data": "x"}, signed)
        without_prefix = signature(
            "POST",
            "https://de.api.io.mi.com/v2/homeroom/gethome",
            {"data": "x"},
            signed,
        )

        assert with_prefix == without_prefix

    def test_given_other_params_when_signed_then_the_signature_differs(self):
        signed = signed_nonce(SSECURITY, NONCE)

        assert signature("POST", URL, {"data": "x"}, signed) != signature(
            "POST", URL, {"data": "y"}, signed
        )


class TestEncryptedParams:
    def test_given_params_when_encrypted_then_the_request_fields_are_complete(self):
        signed = signed_nonce(SSECURITY, NONCE)

        fields = encrypted_params(
            URL, "POST", signed, NONCE, {"data": '{"a": 1}'}, SSECURITY
        )

        assert set(fields) == {"data", "rc4_hash__", "signature", "ssecurity", "_nonce"}
        assert fields["_nonce"] == NONCE
        assert decrypt_payload(signed, fields["data"]) == '{"a": 1}'

    def test_given_params_when_encrypted_then_the_input_is_left_alone(self):
        params = {"data": "x"}

        encrypted_params(
            URL, "POST", signed_nonce(SSECURITY, NONCE), NONCE, params, SSECURITY
        )

        assert params == {"data": "x"}
