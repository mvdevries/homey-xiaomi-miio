from typing import Any

from app.domain.errors import MiioDeviceError


class FakeTransport:
    def __init__(
        self,
        result: Any = None,
        properties: dict[str, Any] | None = None,
        failing: dict[str, int] | None = None,
        failing_methods: dict[str, list[int]] | None = None,
        supports_batch: bool = True,
    ) -> None:
        self.result = result
        self.properties = properties or {}
        self.failing = failing or {}
        self.failing_methods = failing_methods or {}
        self.supports_batch = supports_batch
        self.calls: list[tuple[str, Any]] = []
        self.closed = False

    async def send(
        self, method: str, params: Any = None, *, retries: int | None = None
    ) -> Any:
        self.calls.append((method, params))
        if method == "get_prop":
            self._check_get_prop(params)
        if self.failing_methods.get(method):
            raise MiioDeviceError(self.failing_methods[method].pop(0), "failed")
        if method == "get_prop" and self.properties:
            return [self.properties.get(name) for name in params]
        return self.result

    def _check_get_prop(self, params: list[str]) -> None:
        if len(params) > 1 and not self.supports_batch:
            raise MiioDeviceError(-5001, "invalid arg")
        for name in params:
            if name in self.failing:
                raise MiioDeviceError(self.failing[name], "failed")

    def close(self) -> None:
        self.closed = True
