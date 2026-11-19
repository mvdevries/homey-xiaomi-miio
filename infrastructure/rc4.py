DISCARDED_BYTES = 1024
STATE_SIZE = 256


class Rc4:
    def __init__(self, key: bytes) -> None:
        self._state = self._schedule(key)
        self._i = 0
        self._j = 0
        self.process(bytes(DISCARDED_BYTES))

    def process(self, data: bytes) -> bytes:
        state = self._state
        output = bytearray()
        for byte in data:
            self._i = (self._i + 1) % STATE_SIZE
            self._j = (self._j + state[self._i]) % STATE_SIZE
            state[self._i], state[self._j] = state[self._j], state[self._i]
            key_byte = state[(state[self._i] + state[self._j]) % STATE_SIZE]
            output.append(byte ^ key_byte)
        return bytes(output)

    @staticmethod
    def _schedule(key: bytes) -> list[int]:
        state = list(range(STATE_SIZE))
        j = 0
        for i in range(STATE_SIZE):
            j = (j + state[i] + key[i % len(key)]) % STATE_SIZE
            state[i], state[j] = state[j], state[i]
        return state
