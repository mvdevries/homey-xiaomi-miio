from typing import Any


class FakeHomeyMixin:
    def setup_fake(self, settings=None, capabilities=None) -> None:
        self.settings = dict(
            settings or {"address": "192.0.2.10", "token": "00" * 16, "polling": 5}
        )
        self.capabilities = dict(capabilities or {})
        self.available = True
        self.unavailable_messages: list[str | None] = []
        self.listeners: dict[Any, Any] = {}
        self.errors: list[Any] = []

    def register_multiple_capability_listener(
        self, capability_ids, listener, debounce_timeout=250
    ):
        self.listeners[tuple(capability_ids)] = listener

    def register_capability_listener(self, capability_id, listener):
        self.listeners[capability_id] = listener

    def get_settings(self):
        return self.settings

    def get_setting(self, key):
        return self.settings.get(key)

    def get_capability_value(self, capability):
        return self.capabilities.get(capability)

    async def set_capability_value(self, capability, value):
        self.capabilities[capability] = value

    def get_available(self):
        return self.available

    async def set_available(self):
        self.available = True

    async def set_unavailable(self, message=None):
        self.available = False
        self.unavailable_messages.append(message)

    def error(self, *args):
        self.errors.append(args)
