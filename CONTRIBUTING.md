# Contributing

Thanks for your interest in Xiaomi MiIO for Homey. Bug reports, ideas and pull requests are welcome. This is a
small hobby project, so replies can take a few days.

## Language

Everything in this repository is in English: code, commit messages, pull requests, issues and documentation.
Texts shown to users live in `locales/en.json` and `locales/nl.json`.

## Before you start

- Open an issue first for anything bigger than a small fix, so we can agree on the approach.
- A new device type is welcome: an issue with the model, the miIO properties and the commands is a good start.
- Never put real device names, addresses, tokens or other personal data in issues, tests or code.

## Setting up

You need Node.js, the Homey CLI (`npx homey`), Docker and [uv](https://docs.astral.sh/uv/).

```
uv sync
uv run playwright install chromium
```

Log in once with `npx homey login` and pick a Homey with `npx homey select`.

## Making a change

1. Branch from `main`. The branch name starts with the kind of change, because the release pipeline derives
   the version from it:
   - `breaking/…` for a change that breaks existing users (major version)
   - `feature/…` for a new feature (minor version)
   - `fix/…` for a fix or anything else (patch version)
2. Keep the code style of the project:
   - small functions that do one thing, with descriptive names (too verbose is better than not clear enough)
   - **no comments or docstrings in code**: explain in the pull request or the README instead
   - dependencies point inwards: `domain`, `application`, `infrastructure` (see `CLAUDE.md` for the layout)
3. Add tests. Unit tests for logic, integration tests against the fake miIO device, end-to-end tests for the
   pairing page. Test devices stay generic.
4. Run everything locally:

   ```
   uv run ruff format .
   uv run ruff check .
   uv run pytest
   ```

   Coverage must stay at or above 90%.
5. Open a pull request against `main` with a clear title (it becomes the changelog text) and a description of
   what changed and why. The pull request checks must pass.

Pull requests are squash merged, so the title of the pull request becomes the commit message on `main`.

## Running on a Homey

```
npx homey app validate --level publish
npx homey app run --remote
```

`run` does not reload changed code: stop and start it again after a change. Uploading a build is done by the
release pipeline when a pull request is merged; do not upload by hand.
