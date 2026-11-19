# Xiaomi MiIO for Homey

A Homey app in Python that controls Xiaomi devices over the local miIO protocol (UDP port 54321, AES-128-CBC).
It is the Python successor of the archived Node.js app `homey-xiaomi-archived`. See `README.md` for the
commands. The rules for working in this repository are in `.claude/rules/`.

## Agreements

- **The working language is English**, see `.claude/rules/language.md`. User-facing texts live in
  `locales/en.json` and `locales/nl.json`.
- **Never write comments or docstrings in code**, see `.claude/rules/comments.md`.
- Keep functions small and let them do one thing. Python 3.14 and modern: type hints, dataclasses with
  `slots`, `match`, `asyncio`.
- Changes go through a branch and a pull request, never directly to `main`. Merge only when the maintainer
  says so. No `Co-Authored-By` or other Claude attribution in commits and pull requests.
- Branch names start with `breaking/`, `feature/` or `fix/`.
- Only run the app on the Homey when the maintainer asks (`npx homey app run --remote`, as a background task,
  restart after every code change). Uploading and publishing is only done on explicit request.
- Tests live in `tests/unit`, `tests/integration` and `tests/e2e` (pytest, coverage at least 90%), see
  `.claude/rules/testing.md`. Test devices are generic; never put real devices, tokens or home network
  addresses in them.
- Format and lint with `uv run ruff format .` and `uv run ruff check .`.
- No secrets, tokens, personal data or home network addresses anywhere in the repository.

## Commands

| Task | Command |
|---|---|
| Set up | `uv sync` and `uv run playwright install chromium` |
| Test | `uv run pytest` (all, with coverage), `uv run pytest tests/unit`, `tests/integration`, `tests/e2e` |
| Format and lint | `uv run ruff format .` and `uv run ruff check .` |
| Build and validate | `npx homey app validate --level publish` |
| Start on the Homey | `npx homey app run --remote` (a background task; restart after every change) |

## Project structure

```
app.py             Homey app entry point (stays in the root)
container.py       Wires the implementations into the use cases
domain/            Models, rules, errors and constants, no I/O
application/      The use cases (one class per file) and ports.py, the interfaces they need
infrastructure/    Implements the ports: the miIO UDP transport, packet encoding and encryption
endpoints/         The Homey-facing base classes (polling device and pairing driver)
drivers/<id>/      One folder per device type: device.py, driver.py, driver.compose.json, pair/ and assets/
locales/           Translations: en.json and nl.json
assets/            App icon and store images
tests/             unit/ (domain, application, infrastructure, endpoints, drivers), integration/ and e2e/ (Gherkin
                   features and steps), support/ (fake miIO devices, fake Homey device, harness)
```

## Architecture

The code follows the layers of Clean Architecture. Dependencies only point inwards.

- `domain` imports nothing from the other layers and no Homey SDK or cryptography library.
- `application` only imports `domain` and its own ports, never `infrastructure`, `endpoints` or the Homey SDK.
- `infrastructure` implements the ports. `endpoints`, the driver folders, `container.py` and `app.py` sit on the outside.
- Inner layers import each other with relative imports; the driver folders use absolute `app.` imports.
- An architecture test (`tests/unit/test_architecture.py`) fails if an inner layer imports an outer one.

## Things you need to know

- `app.json` is generated from `.homeycompose/` by the Homey CLI. Change the compose files, then run
  `npx homey app validate --level publish` and commit the regenerated `app.json`.
- The Homey Python SDK is supplied by the Homey runtime; it is not a dependency. Tests stub it in
  `tests/conftest.py`.
- Driver folders contain a hyphen (`yeelink-light-bslamp2`), so tests load them by path
  (`tests/support/__init__.py`). The Homey loads a driver as `app.drivers.<id>.driver`, so driver modules
  import the shared code with absolute `app.` imports.
- Device ids in `data.id` must stay stable: Homey keeps flows and rooms attached to them.
