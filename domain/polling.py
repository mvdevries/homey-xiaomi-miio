DEFAULT_POLLING_SECONDS = 10
MIN_POLLING_SECONDS = 5


def polling_seconds(value: object) -> int:
    return max(int(value or DEFAULT_POLLING_SECONDS), MIN_POLLING_SECONDS)
