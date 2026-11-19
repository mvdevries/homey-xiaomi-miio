# Xiaomi MiIO for Homey

A Homey app in Python that controls Xiaomi devices over the local miIO protocol. `README.md` is for users and
`CONTRIBUTING.md` is for contributors. The rules for working here are in `.claude/rules/`.

## Rules

Each rule is a short file in `.claude/rules/`. Follow them in every task:

- `language.md`: everything in the repository is in English.
- `comments.md`: never add comments or docstrings to code.
- `code-style.md`: small functions, modern Python, respect the layers, use the shared building blocks.
- `testing.md`: every change has tests, coverage at least 90%, generic test devices only.
- `git-and-pull-requests.md`: branch and pull request, branch name prefixes, squash merge, no attribution.
- `running-and-publishing.md`: run on the Homey and upload only when asked.
- `no-secrets-or-personal-data.md`: no secrets, personal data, device names or addresses in the repository.

## Project structure

```
app.py             Homey entry point (stays in the root)
container.py       Wires the implementations into the use cases
domain/            Models, rules, errors and constants, no I/O
application/       The use cases (one class per file) and ports.py, the interfaces they need
infrastructure/    Implements the ports: the miIO UDP transport, packet encoding and encryption
endpoints/         The Homey-facing base classes (polling device and pairing driver)
drivers/<id>/      One folder per device type: device.py, driver.py, driver.compose.json, pair/ and assets/
locales/           Translations: en.json and nl.json
assets/            App icon, store images and the icons of the custom capabilities
tests/             unit/ (domain, application, infrastructure, endpoints, drivers), integration/ and e2e/ (Gherkin
                   features and steps), support/ (fake miIO devices, fake Homey device, harness)
.github/           Workflows (pull request, release, CodeQL) and Dependabot
.homeycompose/     The app manifest, the capabilities and the driver template; app.json is generated from it
```

## Commands

| Task | Command |
|---|---|
| Set up | `uv sync` and `uv run playwright install chromium` |
| Build and validate | `npx homey app validate --level publish` |
| Start on the Homey | `npx homey app run --remote` (a background task; restart after every change) |
| Install permanently | `npx homey app install` |
| Test | `uv run pytest` (all, with coverage), `uv run pytest tests/unit`, `tests/integration`, `tests/e2e` |
| Format and lint | `uv run ruff format .` and `uv run ruff check .` |
| Lint the workflows | `uv tool run --from actionlint-py actionlint` |
| Deploy | Merge a pull request to `main`; the release pipeline does the rest |

Deploying: `.github/workflows/release.yml` runs on every merge to `main` that changes the app (not only docs,
tests or workflows) and can be started by hand. It determines the version from the branch name of the merged
pull request, runs the checks, uploads to Athom in the `production` environment (secret `HOMEY_PAT`) and creates
a tag and GitHub release. The version in the manifest is replaced during the run and not committed.

## Architecture

The code follows the four layers of Clean Architecture. Dependencies only point inwards.

- `domain` imports nothing from the other layers, and no Homey SDK or cryptography library.
- `application` only imports `domain` and its own ports, never `infrastructure`, `endpoints` or the Homey SDK.
- `infrastructure` implements the ports. `endpoints`, the driver folders, `container.py` and `app.py` sit on the
  outside.
- Inner layers import each other with relative imports; the driver folders use absolute `app.` imports.
- An architecture test (`tests/unit/test_architecture.py`) fails if an inner layer imports an outer one.

Shared building blocks, use these instead of writing new ones:

- `MiioPollingDevice` for polling, availability, the settings and the `commands` table of a device
  (`endpoints/polling_device.py`)
- `MiioDriver` for pairing (`endpoints/pairing_driver.py`)
- `MiioService` as the base of the services, and `read_properties` to read properties in one request with a
  fallback (`application/device_service.py`, `application/properties.py`)
- `.homeycompose/drivers/templates/miio-device.json` for the settings, the pairing view and the other shared
  parts of the driver manifests

A new device type is a `domain` module (state, parser and the capability mapping), a service, a `device.py` with a
`commands` table and the driver folder with its manifest, pairing view and assets.

## Homey platform

- The Homey runtime loads a driver as `app.drivers.<id>.driver`. Driver folders contain a hyphen, so tests load
  them by path (`tests/support/__init__.py`) and driver modules import shared code with absolute `app.`
  imports. The Homey Python SDK is supplied by the runtime; it is not a dependency. Tests stub it in
  `tests/conftest.py`.
- `app.json` is generated from `.homeycompose/` by the Homey CLI. Change the compose files, then run
  `npx homey app validate --level publish` and commit the regenerated `app.json`.
- The `driver.compose.json` files extend a template. The `pair/pair.html` files cannot be shared by Homey, so a
  test keeps the copies identical.
- Device ids in `data.id` must stay stable: Homey keeps flows and rooms attached to them.
- The app icon (`assets/icon.svg`) and the driver icons are transparent line drawings on a 960 x 960 canvas that
  uses the whole canvas; filled pictures, gradients and background colours are not allowed by the app store
  guidelines. The images are PNG: 250 x 175, 500 x 350 and 1000 x 700 for the app, 75, 500 and 1000 square with a
  white background for a driver.
- A custom enum capability is shown as a list (picker); a number capability can be a slider and a boolean a
  toggle. Use those when several controls must be visible at once. Custom capabilities can have an `icon`.
- The Homey CLI asks for confirmations in an interactive session. Run it with `HOMEY_HEADLESS=1` to skip them,
  as the pipeline does.

## miIO devices

- A device is reached over UDP port 54321 with a handshake (hello packet) and AES-128-CBC encrypted JSON. The
  token (32 hexadecimal characters) is needed to talk to it; a wrong token looks the same as no answer.
- Packets get lost. The transport sends again with a new message id and the pairing probes up to three times.
  Requests to one device are sent one at a time; sending them in parallel loses answers.
- Read all properties of a device in one `get_prop`. The standing fan and the humidifier accept that; the
  documentation says they answer only one property per request, so `read_properties` falls back to one request
  per property.
- The standing fan refuses an oscillation angle above 120 (`-5001 invalid arg`). The humidifier answers `-6011`
  when a mode is set while it is off, so the service switches it on and sends the mode again.
- The tokens and addresses of real devices never go into the repository. Test devices are the fake devices in
  `tests/support/fake_miio_devices.py`.

## Pairing page

- Homey puts its own styles on `label`, `button` and `input` (capitals, padding, height). The pairing views use the
  look of the settings pages of homeykit (`.text-input`, `.number-input`, `.button`, the toast). The `hidden`
  attribute only works because of the rule `[hidden] { display: none !important }`.
- Errors from the backend are codes (`token_invalid`, `device_unreachable`); the page translates them through
  `pair.errors.<code>` in the locale files.

## Pipelines

- Pull requests run lint and formatting (ruff and actionlint), all tests with coverage, a build validation and a
  branch name check.
- Dependabot groups minor and patch updates in one pull request per ecosystem and major updates in a separate
  one.
- The Homey CLI runs directly on the runner (it needs Docker and QEMU); the Athom actions do not work for a
  Python app.
- The repository is private, so a job that reads pull requests needs the `pull-requests: read` permission
  (homeykit is public and does not).
