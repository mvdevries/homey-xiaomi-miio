FAILURES_BEFORE_UNAVAILABLE = 3


def failure_limit(connected: bool) -> int:
    return FAILURES_BEFORE_UNAVAILABLE if connected else 1


def should_mark_unavailable(failures: int, connected: bool) -> bool:
    return failures >= failure_limit(connected)
