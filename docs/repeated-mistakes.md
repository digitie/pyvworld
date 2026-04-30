# Repeated Mistakes

이 문서는 구현 중 반복하기 쉬운 실수를 막기 위한 운영 메모입니다. 새 실수를 발견하면 테스트와 함께 이 문서를 갱신합니다.

## 1.0 문서를 섞지 말 것

VWorld 레퍼런스에는 1.0과 2.0 링크가 함께 있습니다. 검색, Geocoder, 2D데이터, 범례이미지, StaticMap은 반드시 2.0 문서의 파라미터와 URL만 사용합니다.

예외: WMS/WFS의 `VERSION=1.3.0`/`1.1.0`, WMTS/TMS 경로의 `/1.0.0/`은 OGC 서비스 버전입니다. VWorld API 1.0 구현이 아닙니다.

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

## StaticMap 크기와 줌

StaticMap 문서 기준:

- `zoom`: 6~18
- `size`: 최대 `1024,1024`

초과 요청은 서버에 보내기 전에 `VworldInvalidParameterError`로 막습니다.

## 해외위성영상 테마 타일 확장자

일반 `Satellite` 타일은 `jpeg`가 기본이지만, 공식 해외위성영상 예시는 `png`입니다. 테마 타일은 `png`, `jpeg`, `jpg`를 허용합니다.
