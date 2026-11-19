# Xiaomi MiIO for Homey

A Homey app written in Python that controls Xiaomi devices over the local miIO protocol, without a cloud.

## Supported devices

- Mi Bedside Lamp 2 (`yeelink.light.bslamp2`): on/off, brightness, hue, saturation, colour temperature, mode
- Mi Smart Standing Fan (`zhimi.fan.za4`): on/off, speed, natural wind, oscillation and angle, LED display, buzzer,
  child lock
- Mi Smart Humidifier (`zhimi.humidifier.ca1`, `cb1`): on/off, mode, target humidity, dry mode, humidity and
  temperature, LED display, buzzer, child lock. Only tested against a fake device so far

## Adding a device

Pairing asks for a name, the IP address and the device token (32 hexadecimal characters). The app checks that the
device answers before it is added. The token can be read from your Xiaomi account, for example with
[Xiaomi-cloud-tokens-extractor](https://github.com/PiotrMachowski/Xiaomi-cloud-tokens-extractor).

## Development

Requires Node.js, the Homey CLI (`npx homey`), a running Docker and [uv](https://docs.astral.sh/uv/). Log in
once with `npx homey login` and pick a Homey with `npx homey select`.

```bash
npx homey app validate --level publish
npx homey app run --remote
```

`run` does not reload changed code: stop and start it again after a change.

```bash
uv sync
uv run playwright install chromium
uv run ruff format .
uv run ruff check .
uv run pytest
```

The unit tests mirror the layers (`domain`, `application`, `infrastructure`, `endpoints`). The integration tests run
the real code against a fake miIO device and the end-to-end tests drive the pairing page in a browser; both are
Gherkin scenarios. See `CLAUDE.md` for the project structure and the architecture.

## License

MIT, see [LICENSE](LICENSE).
