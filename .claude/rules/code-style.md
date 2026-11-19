# Rule: code style

- Keep functions small and let them do one thing. A name describes what the function does; too verbose is
  better than not clear enough.
- Python 3.14 and modern: type hints, dataclasses with `slots`, `match`, `Protocol`, `asyncio`.
- Respect the layers: `domain` → `application` → `infrastructure`, with dependencies only pointing inwards (see
  `CLAUDE.md`). An architecture test enforces this.
- Use the shared building blocks (the `commands` table and `MiioPollingDevice`, `MiioService`, `MiioDriver`)
  instead of writing a new copy of what they do.
- User-facing texts live in `locales/en.json` and `locales/nl.json`, never hardcoded in the pairing views.
- Format and lint with ruff before every commit; the pipeline fails otherwise.
