RECOVERABLE_ERROR_CODES = frozenset({-30001, -9999})


class MiioError(Exception):
    pass


class InvalidTokenError(MiioError):
    pass


class MalformedPacketError(MiioError):
    pass


class MiioTimeoutError(MiioError):
    pass


class MiioDeviceError(MiioError):
    def __init__(self, code: int, message: str) -> None:
        super().__init__(f"miIO error {code}: {message}")
        self.code = code

    @property
    def recoverable(self) -> bool:
        return self.code in RECOVERABLE_ERROR_CODES


class MiioConnectionError(MiioError):
    pass


class CloudError(Exception):
    pass


class CloudRequestError(CloudError):
    pass


class CloudTimeoutError(CloudError):
    pass


class LoginExpiredError(CloudError):
    pass


class LoginFailedError(CloudError):
    pass


class NotSignedInError(CloudError):
    pass
