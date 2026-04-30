# VWorld API Notes

기준 문서: [VWorld API 레퍼런스](https://www.vworld.kr/dev/v4apiRefer.do)

이 파일은 구현자가 빠르게 확인할 수 있도록 공식 문서의 Python HTTP 클라이언트 구현 포인트만 압축한 메모입니다. 자세한 파라미터는 공식 문서를 우선합니다.

## 구현 대상

| API | 공식 문서 | pyvworld 메서드 |
|---|---|---|
| 검색 API 2.0 | `/dev/v4dv_search2_s001.do` | `search`, `search_place`, `search_address`, `search_district`, `search_road` |
| Geocoder API 2.0 | `/dev/v4dv_geocoderguide2_s001.do`, `s002.do` | `get_coord`, `geocode`, `get_address`, `reverse_geocode` |
| 2D데이터 API 2.0 | `/dev/v4dv_2ddataguide2_s001.do` | `get_data_feature`, `get_data_feature_type` |
| WMS/WFS API 2.0 레퍼런스 | `/dev/v4dv_wmsguide2_s001.do` | WMS/WFS 메서드 |
| 범례이미지 API 2.0 | `/dev/v4dv_legendguide2_s001.do` | `get_legend_graphic`, `get_legend_style` |
| StaticMap API 2.0 | `/dev/v4dv_static2_s001.do` | `static_map`, `static_map_url` |
| WMTS/TMS API | `/dev/v4dv_wmtsguide_s001.do`, `/dev/v4dv_tmsguide_s001.do` | WMTS/TMS URL 및 fetch 메서드 |

## 공통 규칙

- REST 계열은 `version=2.0`을 고정한다.
- `format=json`, `errorformat=json`을 기본값으로 둔다.
- VWorld 오류 응답은 `response.status == "ERROR"`와 `response.error.code`를 기준으로 예외 매핑한다.
- `response.status == "NOT_FOUND"`는 `VworldNoDataError`로 변환한다.
- WMS/WFS의 `VERSION=1.3.0` 또는 `1.1.0`은 OGC 프로토콜 버전이며 VWorld API 1.0 구현이 아니다.
- WMTS/TMS의 경로 `/1.0.0/`도 OGC 타일 서비스 경로 버전이다. 공식 문서에 2.0 대체 경로가 없다.

## 2D 데이터 서비스 카탈로그

공식 2D데이터 API 2.0 목록은 2026-05-01 기준 158건입니다. `pyvworld.catalog.DATA_SERVICES`와 [docs/data-services.md](docs/data-services.md)에 고정해 두었습니다.

카탈로그는 서비스 ID 조회 보조용입니다. API 호출 자체는 공식 `/req/data` 엔드포인트 하나를 사용하며, `data=`에 서비스 ID를 넣습니다.

## SDK 문서와 HTTP 엔드포인트 경계

VWorld API 레퍼런스에는 2D 지도 JavaScript API, WebGL 3D 지도 API, 3D 분석/시뮬레이션 API, 모바일 API, 데스크톱 API도 함께 있습니다. 이들은 Python에서 HTTP GET으로 호출하는 데이터 엔드포인트가 아니라 브라우저/앱 런타임 SDK 레퍼런스입니다.

따라서 이 저장소에서는 URL이 명시된 REST/OGC/타일/이미지 엔드포인트를 래핑하고, SDK별 클래스/이벤트/렌더링 API는 구현 대상에서 제외합니다.
