from .token import token_from_hex
from .transport import MiioTransport

PROBE_RETRIES = 2


async def probe_device(address: str, token_hex: str) -> None:
    transport = MiioTransport(address, token_from_hex(token_hex))
    try:
        await transport.send("miIO.info", retries=PROBE_RETRIES)
    finally:
        transport.close()
