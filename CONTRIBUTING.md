# Contributing

## Development Setup

```bash
pip install -e ".[dev]"
```

## Checks

Run these before committing:

```bash
python -m compileall src/vworld tests
python -m pytest
python -m ruff check .
python -m mypy src/vworld
```

## API Changes

- Verify the official VWorld reference page first.
- Prefer VWorld 2.0 documentation when both 1.0 and 2.0 exist.
- Keep HTTP error mapping in `src/vworld/_http.py`.
- Add offline tests with exact URL/query assertions.
- Update `docs/api-coverage.md` and `docs/repeated-mistakes.md` when behavior changes.
