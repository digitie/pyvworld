# Repeated Mistakes

이 문서는 구현 중 반복하기 쉬운 실수를 막기 위한 운영 메모입니다. 새 실수를 발견하면 테스트와 함께 이 문서를 갱신합니다.

## PowerShell 파일 검색과 UTF-8 출력

이 작업 환경에서는 `rg`가 실행 권한 문제로 막힐 수 있습니다. 파일 목록과 검색은 `Get-ChildItem -Recurse -File`, `Select-String` 같은 PowerShell 명령으로 우회합니다.

Markdown과 문서는 UTF-8입니다. PowerShell 기본 출력으로 한글이 깨져 보이면 문서 내용 문제가 아니라 출력 인코딩 문제일 수 있으므로 `Get-Content -Encoding UTF8`처럼 인코딩을 명시합니다.

## 문서 경로와 Python 내부 문서 언어

문서에 파일 위치를 남길 때는 `docs/api-coverage.md`처럼 프로젝트 기준 상대 경로를 사용합니다. 드라이브 문자나 홈 디렉터리가 포함된 개인 로컬 절대 경로는 문서에 남기지 않습니다.

Python docstring과 주석 같은 내부 문서도 한글로 작성합니다. 새 공개 헬퍼를 추가할 때 영어 docstring을 그대로 두지 않습니다.

## 1.0 문서를 섞지 말 것

VWorld 레퍼런스에는 1.0과 2.0 링크가 함께 있습니다. 검색, Geocoder, 2D데이터, 범례이미지, StaticMap은 반드시 2.0 문서의 파라미터와 URL만 사용합니다.

예외: WMS/WFS의 `VERSION=1.3.0`/`1.1.0`, WMTS/TMS 경로의 `/1.0.0/`은 OGC 서비스 버전입니다. VWorld API 1.0 구현이 아닙니다.

## 얇은 wrapper로 우회하지 말 것

다른 라이브러리에 이미 검증된 구현이 있으면 단순 wrapper를 하나 더 쌓아 문제를 미루지 않습니다. 작은 수정만 고집하는 것보다 동작이 맞는 구현 방식을 현재 구조에 직접 반영하는 편을 우선합니다.

가져올 때는 라이선스와 출처를 확인하고, 이 프로젝트의 공개 메서드가 맡아야 하는 파라미터 검증, URL/요청 조립, `_http.py` 오류 매핑 경계를 유지합니다. 차이가 생기는 부분은 테스트와 문서에 남깁니다.

## 인증키를 두 번 넣지 말 것

REST/OGC/Image 엔드포인트는 `key=` 쿼리 파라미터를 사용합니다. WMTS/TMS는 키가 경로 안에 들어갑니다.

실수하면 타일 URL이 `/test-key/...png?key=test-key`처럼 됩니다. `get_wmts_tile`, `get_tms_tile` 테스트가 이 문제를 막습니다.

## 주소/좌표 변환 요청명을 섞지 말 것

- 주소에서 좌표: `request=getcoord`, 필수 `address`, `type=road|parcel`
- 좌표에서 주소: `request=getaddress`, 필수 `point=x,y`, `type=road|parcel|both`

두 API 모두 `/req/address`를 사용하므로 요청명 실수가 잘 납니다.

## Search category 필수 조건

검색 API에서 `type=address`와 `type=district`는 `category`가 필수입니다. `place`는 선택이고, `road`는 category를 쓰지 않습니다.

## 2D Data service ID는 숫자가 아니다

`LT_C_ADEMD_INFO`, `LP_PA_CBND_BUBUN` 같은 서비스 ID는 문자열 그대로 유지합니다. 대소문자나 prefix를 임의로 바꾸지 않습니다.

## `attrFilter` 구분자

공식 문서의 조건식 내부 구분자는 `:`이고 여러 조건 구분자는 `|`입니다. `columns`와 `category`처럼 쉼표로 합치면 다른 조건식이 됩니다. list 입력은 `|`로 합치고, 복잡한 필터는 문자열 그대로 넘기는 것을 권장합니다.

## 이미지 오류도 JSON일 수 있다

범례/StaticMap/WMS 이미지 요청에서 오류 응답이 이미지가 아니라 JSON/XML일 수 있습니다. `_http.py`는 바이너리 요청에서도 JSON 오류 payload를 검사합니다.

## httpx 전환 후 requests 전용 mock을 쓰지 말 것

HTTP 계층은 `httpx` 기반입니다. 기본 테스트에서 `responses`처럼 `requests` 전용 mock을 쓰면 실제 호출 경로를 검증하지 못합니다. 새 HTTP 테스트는 `tests/conftest.py`의 `HttpxMock` 헬퍼를 사용하고, 동기/비동기 클라이언트 모두 `_http.py`의 오류 매핑을 통과하게 만듭니다.

## StaticMap 크기와 줌

StaticMap 문서 기준:

- `zoom`: 6~18
- `size`: 최대 `1024,1024`
- `basemap`: `NONE`, `GRAPHIC`, `GRAPHIC_WHITE`, `GRAPHIC_NIGHT`, `PHOTO`, `PHOTO_HYBRID`
- `format`: `png`, `jpeg`, `bmp`

초과 요청은 서버에 보내기 전에 `VworldInvalidParameterError`로 막습니다.

## 해외위성영상 테마 타일 확장자

일반 `Satellite` 타일은 `jpeg`가 기본이지만, 공식 해외위성영상 예시는 `png`입니다. 테마 타일은 `png`, `jpeg`, `jpg`를 허용합니다.

## WMS/WFS domain 파라미터

REST API는 키만으로도 동작하는 경우가 많지만, WMS/WFS는 인증키와 `domain=` 조합에 민감합니다. 같은 키라도 실제 도메인 값, 빈 `domain=`, domain 생략 중 어느 쪽이 통과하는지가 엔드포인트마다 달라질 수 있습니다.

규칙: `domain=None`은 클라이언트 기본 domain을 사용하고, 메서드에 `domain=""`을 넘기면 빈 `domain=` 쿼리를 보냅니다. 환경 변수 domain을 완전히 억제하려면 `VworldClient(api_key, domain="")`처럼 별도 클라이언트를 만들고 메서드에는 `domain`을 넘기지 않습니다. 라이브 테스트에서 이 차이를 반복해서 확인합니다.

## 인증키 노출 방지

라이브 테스트 실패 로그에 `_VworldHttp(api_key=...)` 형태로 키가 찍히면 안 됩니다. `_VworldHttp`의 `api_key`는 repr에서 제외하고, 테스트/문서에는 원문 키가 들어간 URL을 남기지 않습니다.

로그, 캐시 키, 메타데이터를 만들 때도 원본 요청 파라미터를 그대로 저장하지 않습니다. `sanitize_request_params()`는 `key`, `api_key`, `serviceKey` 계열 키를 제거하고, `redact_credentials_in_text()`는 쿼리 `key=`와 `/req/wmts|tms/1.0.0/{key}/...` 경로 키를 마스킹합니다.

## 페이지 반복 시 무한 루프 방지

Search/2D Data 응답에는 공식적으로 `response.page.total/current/size`와 `response.record.total/current`가 있습니다. 전체 페이지를 따라갈 때는 직접 `while True`를 쓰지 말고 `iter_search_pages`, `iter_data_feature_pages`, 또는 `iter_pages()`의 `max_pages`/`max_items` 가드를 사용합니다.

## 위경도 순서 혼동

VWorld `point`는 항상 `x,y` 순서입니다. EPSG:4326에서 `x,y`는 `lon,lat`입니다. 사용자가 “위경도”라고 말하면 보통 `lat,lon` 순서로 생각하므로 공개 예제와 새 코드에서는 `latlon(lat, lon)` 또는 `LatLon(lat=..., lon=...)`을 우선 사용합니다. 기존 튜플 `(lon, lat)` 지원은 호환성을 위해 유지합니다.

## Pydantic 적용 시 예외 타입 유지

공개 값 객체는 Pydantic v2 모델이지만, 좌표 범위/순서 오류는 기존 public API와 맞게 `VworldInvalidParameterError`를 유지합니다. Pydantic `ValidationError`는 frozen 모델 변경처럼 Pydantic 자체 계약 위반에만 기대합니다.
