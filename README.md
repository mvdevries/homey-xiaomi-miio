# Xiaomi MiIO for Homey

A Homey app written in Python that controls Xiaomi devices over the local miIO protocol, without a cloud.

Status: skeleton. The app starts, the Mi Bedside Lamp 2 driver can be paired (address and token are
validated), but the miIO protocol and the device control are not implemented yet.

## Planned devices

- Mi Bedside Lamp 2 (`yeelink.light.bslamp2`): on/off, brightness, hue, saturation, colour temperature, mode
- Mi Standing Fan (`zhimi.fan.sa1`): on/off, speed, natural wind

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
uv run ruff format .
uv run ruff check .
uv run pytest
```

## License

MIT, see [LICENSE](LICENSE).
