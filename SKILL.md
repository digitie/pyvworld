---
name: pyvworld-builder
description: Use this skill when building, extending, testing, or documenting the pyvworld Python client for VWorld REST, OGC, image, WMTS, or TMS APIs.
---

# pyvworld Builder

## Read First

1. `vworld-api.md`
2. `docs/api-coverage.md`
3. `docs/repeated-mistakes.md`

## Invariants

- Search, Geocoder, 2D Data, Legend, and StaticMap use VWorld API 2.0 only.
- WMS/WFS OGC protocol versions are not VWorld API 1.0.
- WMTS/TMS put the key in the path, not in a query parameter.
- Default tests must be offline.
- `pyvworld/_http.py` owns error mapping.

## Required Checks

```bash
python -m compileall pyvworld tests
python -m pytest
python -m ruff check .
python -m mypy pyvworld
```

## Adding an Endpoint

1. Confirm the official VWorld page and version.
2. Add a method to `VworldClient`.
3. Add request parameter validation before the HTTP call.
4. Add tests that assert exact path/query shape.
5. Update `docs/api-coverage.md` and README when user-facing.
6. Add any new gotcha to `docs/repeated-mistakes.md`.
