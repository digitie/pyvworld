# API Coverage

이 문서는 현재 `pyvworld`가 어떤 VWorld API를 구현했는지, 무엇을 의도적으로 제외했는지 기록합니다.

## Implemented

| Area | Endpoint | Version rule | Methods |
|---|---|---|---|
| Search | `https://api.vworld.kr/req/search` | 2.0 only | `search*` |
| Geocoder | `https://api.vworld.kr/req/address` | 2.0 only | `get_coord`, `get_address` |
| 2D Data | `https://api.vworld.kr/req/data` | 2.0 only | `get_data_feature`, `get_data_feature_type` |
| WMS | `https://api.vworld.kr/req/wms` | VWorld 2.0 reference, OGC WMS 1.3.0 | `wms_get_capabilities`, `wms_get_map`, `wms_get_feature_info` |
| WFS | `https://api.vworld.kr/req/wfs` | VWorld 2.0 reference, OGC WFS 1.1.0 | `wfs_get_capabilities`, `wfs_describe_feature_type`, `wfs_get_feature` |
| Legend Image | `https://api.vworld.kr/req/image` | 2.0 only | `get_legend_graphic`, `get_legend_style` |
| StaticMap | `https://api.vworld.kr/req/image` | 2.0 only | `static_map`, `static_map_url` |
| WMTS | `/req/wmts/1.0.0/{key}/...` | official WMTS path only | `wmts_*` |
| TMS | `/req/tms/1.0.0/{key}/...` | official TMS path only | `tms_*` |

## Public Types

Public wrappers accept the original string values and typed helpers. Enums cover common documented parameter sets such as search/address categories, CRS, legend type, image format, StaticMap basemap, and tile layers. `LatLon`, `LonLat`, `BBox`, `BinaryResponse`, and `TextResponse` are frozen Pydantic v2 models, so external programs can use `model_validate()`, `model_dump()`, and JSON schema generation without changing existing tuple inputs.

## Not Implemented

These are not Python HTTP endpoint wrappers:

- 2D지도 API JavaScript SDK
- WebGL 3D지도 JavaScript SDK
- 3D분석ㆍ시뮬레이션 JavaScript SDK
- 2D/3D 모바일 SDK references
- 3D 데스크톱 SDK references
- 배경지도 API 1.0, 벡터지도 API 1.0

If a future VWorld page exposes a stable HTTP endpoint for one of these areas, add it as a normal method and update this file with the official URL.

## 2D Data Catalog

- Official list count: 158 entries
- Generated date: 2026-05-01
- Code: `pyvworld/catalog.py`
- Markdown: `docs/data-services.md`

All catalog entries have `version == "2.0"`. Tests assert the count and a few sentinel IDs to catch accidental truncation.
