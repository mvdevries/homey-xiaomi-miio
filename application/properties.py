from collections.abc import Iterable
from typing import Any

from ..domain.errors import MiioDeviceError
from .ports import DeviceTransport


async def read_properties(
    transport: DeviceTransport,
    names: Iterable[str],
    optional: frozenset[str] = frozenset(),
) -> dict[str, Any]:
    names = list(names)
    batch = await _read_batch(transport, names)
    if batch is not None:
        return batch
    return {
        name: await _read_property(transport, name, name in optional) for name in names
    }


async def _read_batch(
    transport: DeviceTransport, names: list[str]
) -> dict[str, Any] | None:
    try:
        result = await transport.send("get_prop", names)
    except MiioDeviceError:
        return None
    if not isinstance(result, list) or len(result) != len(names):
        return None
    return dict(zip(names, result, strict=True))


async def _read_property(transport: DeviceTransport, name: str, optional: bool) -> Any:
    try:
        result = await transport.send("get_prop", [name])
    except MiioDeviceError:
        if optional:
            return None
        raise
    return result[0] if isinstance(result, list) and result else None
