# Testing

The default test suite must not call the live VWorld service. Use `responses` for HTTP tests and exact URL/query assertions.

## Required Checks

```bash
python -m compileall pyvworld tests
python -m pytest
python -m ruff check .
python -m mypy pyvworld
```

## Test Strategy

- Parameter tests cover bool conversion, CSV joining, bbox/point formatting, and invalid sizes.
- HTTP tests cover key injection, JSON parsing, VWorld error code mapping, `NOT_FOUND`, binary JSON error payloads, retries, and network timeouts.
- REST client tests assert `version=2.0` and endpoint-specific required params.
- OGC tests assert WMS/WFS uppercase parameter names and response wrappers.
- Image/tile tests assert StaticMap, legend, WMTS, and TMS URL shapes.
- Catalog tests assert the official 158-entry count and all entries being 2.0.

## Live Tests

Live tests should be opt-in only:

- Mark them with `@pytest.mark.live`.
- Skip unless `VWORLD_API_KEY` is present.
- Do not store raw responses containing private keys or query URLs with keys.
- Prefer small requests such as one geocoder call or one tiny StaticMap.

No live tests are currently required for the default validation path.
