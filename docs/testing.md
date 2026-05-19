# Testing

The default test suite must not call the live VWorld service. Use the local `httpx.MockTransport` helper in `tests/conftest.py` for HTTP tests and exact URL/query assertions.

## Required Checks

```bash
python -m compileall src/vworld tests
python -m pytest
python -m ruff check .
python -m mypy src/vworld
```

## Test Strategy

- Parameter tests cover bool conversion, CSV joining, bbox/point formatting, and invalid sizes.
- HTTP tests cover key injection, JSON parsing, VWorld error code mapping, `NOT_FOUND`, binary JSON error payloads, retries, and network timeouts.
- Async client tests cover `AsyncVworldClient`, the `VworldClient.aio()` factory, and blank-domain preservation.
- REST client tests assert `version=2.0` and endpoint-specific required params.
- OGC tests assert WMS/WFS uppercase parameter names and response wrappers.
- Image/tile tests assert StaticMap, legend, WMTS, and TMS URL shapes.
- Catalog tests assert the official 158-entry count and all entries being 2.0.
- Pagination tests cover `response.page` traversal, item extraction, and loop guards.
- Metadata tests cover credential sanitization for query `key=` and WMTS/TMS path keys.
- Debug UI fixture tests cover sensitive value redaction and overwrite protection.
- Generated fixture replay tests load `tests/fixtures/**/*.json`, parse the stored raw response, run the matching processor, and compare processed output without live network calls.
- Catalog tests cover debug API catalog entries, service key issuance URL exposure, and human-readable data service labels.
- REST client tests cover whitespace normalization for pasted VWorld service keys.

## Live Tests

Live tests should be opt-in only:

- Mark them with `@pytest.mark.live`.
- Skip unless `VWORLD_API_KEY` is present.
- Do not store raw responses containing private keys or query URLs with keys.
- Prefer small requests such as one geocoder call or one tiny StaticMap.
- Endpoint-specific VWorld key/domain rejection may be skipped for live-only smoke tests, but Search/Geocoder and async Search should still pass with a usable key.

No live tests are currently required for the default validation path.

## Fixture Replay

Debug UI fixtures are stored under `tests/fixtures/{function}/{case}.json`. The common runner in `tests/test_generated_fixtures.py` maps each `function` to parser/processor callables in `tests/runners.py`.

Supported assertion modes:

- `snapshot`: compare processed output, excluding keys listed in `assertion.exclude_fields`.
- `schema_only`: assert parsing and processing completed.
- `required_fields`: assert dot-separated fields exist in processed output.

Fixtures must not store VWorld API keys, Authorization headers, access tokens, refresh tokens, or tile path keys. The debug UI writer masks these values before writing JSON.

## Current Live Verification

The live smoke suite is in `tests/test_live_api.py`.

Run it with a local `.env` file or exported environment variables:

```bash
python -m pytest -m live
```

Recommended local `.env`:

```bash
VWORLD_API_KEY="issued-key"
VWORLD_DOMAIN="registered-domain"
```

Live domain behavior is not uniform across VWorld endpoints. During local verification on 2026-05-06, Search, Geocoder, image, WMTS, and TMS worked with the issued key. WMS/WFS capabilities were most reliable with an explicit blank `domain=` query, while the 2D Data smoke test used a client whose default domain was suppressed. The live tests retry short smoke calls because VWorld can intermittently return `INCORRECT_KEY` for the same key and request shape.
