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
- Tests live in `tests/unit` (pytest, coverage at least 90%). Test devices are generic; never put real
  devices, tokens or home network addresses in them.
- Format and lint with `uv run ruff format .` and `uv run ruff check .`.
- No secrets, tokens, personal data or home network addresses anywhere in the repository.

## Things you need to know

- `app.json` is generated from `.homeycompose/` by the Homey CLI. Change the compose files, then run
  `npx homey app validate --level publish` and commit the regenerated `app.json`.
- The Homey Python SDK is supplied by the Homey runtime; it is not a dependency. Tests stub it in
  `tests/conftest.py`.
- Driver folders contain a hyphen (`yeelink-light-bslamp2`), so tests load them by path
  (`tests/support.py`). How driver modules import shared project code at runtime is not verified yet.
- Device ids in `data.id` must stay stable: Homey keeps flows and rooms attached to them.
