# python-vworld-api

VWorld(브이월드) HTTP API를 Python에서 쓰기 쉽게 감싼 비공식 클라이언트입니다.

이 패키지는 VWorld 공식 [API 레퍼런스](https://www.vworld.kr/dev/v4apiRefer.do)를 기준으로, Python에서 직접 호출 가능한 REST/OGC/타일 엔드포인트를 함수로 제공합니다. 1.0과 2.0 문서가 함께 있는 API는 2.0만 구현했습니다.

## 특징

- 검색 API 2.0: 장소, 주소, 행정구역, 도로명 검색
- Geocoder API 2.0: 주소 좌표 변환, 좌표 주소 변환
- 2D데이터 API 2.0: `GetFeature`, `GetFeatureType`, 공식 서비스 ID 158건 카탈로그
- WMS/WFS API 2.0 레퍼런스: `GetCapabilities`, `GetMap`, `GetFeatureInfo`, `DescribeFeatureType`, `GetFeature`
- 범례이미지/StaticMap API 2.0: 이미지 바이트 응답과 URL 빌더
- WMTS/TMS: 타일, 해외위성영상 테마 타일, capabilities/resource URL
- 페이지 반복/아이템 추출 헬퍼와 인증키를 제거한 메타데이터/캐시 키 유틸
- 네트워크 없이 검증되는 fixture/mock 기반 테스트

JS 지도 SDK, WebGL 3D 지도 SDK, 모바일/데스크톱 SDK는 Python HTTP 엔드포인트가 아니라 런타임 SDK 문서이므로 이 패키지의 함수 래핑 범위에서 제외했습니다. 범위와 근거는 [docs/api-coverage.md](docs/api-coverage.md)에 정리했습니다.

## 설치

```bash
pip install python-vworld-api
```

개발 중인 로컬 저장소에서는:

```bash
pip install -e ".[dev]"
```

## 인증키

VWorld 인증키를 환경변수에 넣습니다.

```bash
export VWORLD_API_KEY="발급받은_인증키"
```

PowerShell:

```powershell
$env:VWORLD_API_KEY="발급받은_인증키"
```

도메인 파라미터가 필요한 환경에서는 `VWORLD_DOMAIN`, `VworldClient.from_env_file()`, 또는 클라이언트 생성자의 `domain=`을 사용합니다. 엔드포인트별로 VWorld의 도메인 검증 동작이 다를 수 있어, 특정 호출에서만 바꾸려면 메서드의 `domain=` 인자를 사용합니다.

## 사용 예시

```python
from vworld import VworldClient

client = VworldClient.from_env()

result = client.search_address("성남시 분당구 판교로 242")
print(result["response"]["result"]["items"])

coord = client.geocode("판교로 242", type="road")
print(coord["response"]["result"]["point"])

reverse = client.reverse_geocode((127.101313354, 37.402352535), type="both")
print(reverse["response"]["result"])
```

로컬 `.env` 파일에서 바로 읽을 수도 있습니다. `.env`는 `.gitignore`에 포함되어 커밋되지 않습니다.

```bash
VWORLD_API_KEY="발급받은_인증키"
VWORLD_DOMAIN="인증키에 등록한_도메인"
```

```python
client = VworldClient.from_env_file()
```

## 타입/좌표 모델

외부 프로그램에서 문자열 상수를 직접 외우지 않아도 되도록 주요 파라미터 enum을 제공합니다. 기존 문자열 호출은 그대로 동작합니다. 공개 값 객체는 Pydantic v2 `BaseModel` 기반이라 `model_validate()`, `model_dump()`, `model_json_schema()`로도 다룰 수 있습니다.

```python
from vworld import (
    AddressCategory,
    AddressType,
    Crs,
    ImageFormat,
    SearchType,
    StaticMapBase,
    VworldClient,
    bbox_from_latlon,
    latlon,
)

client = VworldClient.from_env_file()

client.search(
    "판교",
    SearchType.ADDRESS,
    category=AddressCategory.ROAD,
    bbox=bbox_from_latlon(south=37.3, west=126.9, north=37.6, east=127.2),
    crs=Crs.WGS84,
)

client.geocode("판교로 242", type=AddressType.ROAD)
client.reverse_geocode(latlon(37.402352535, 127.101313354))

client.static_map_url(
    center=latlon(37.566643, 126.978271),
    zoom=16,
    size=(400, 400),
    basemap=StaticMapBase.PHOTO_HYBRID,
    format=ImageFormat.PNG,
)

payload = latlon(37.402352535, 127.101313354).model_dump()
```

VWorld의 `point` 파라미터는 `x,y` 순서입니다. `EPSG:4326`에서는 `x=lon`, `y=lat`이므로 일반적인 “위경도” 입력은 `latlon(lat, lon)` 또는 `LatLon(lat=..., lon=...)`을 쓰는 것을 권장합니다. 기존 `(lon, lat)` 튜플도 계속 지원합니다.

`StaticMapBase`와 `ImageFormat`은 공식 문서의 값(`NONE`, `GRAPHIC_WHITE`, `GRAPHIC_NIGHT`, `PHOTO_HYBRID`, `bmp` 등)을 포함합니다. 기존에 쓰기 쉬운 이름으로 넣었던 `StaticMapBase.HYBRID`는 `PHOTO_HYBRID` 별칭으로 유지합니다.

2D 데이터 API:

```python
from vworld import VworldClient, get_data_service

client = VworldClient.from_env(domain="example.com")
service = get_data_service("LT_C_ADEMD_INFO")

features = client.get_data_feature(
    service.service_id,
    attr_filter="emd_cd:=:11650108",
    geometry=False,
    columns=["emd_cd", "full_nm"],
)
print(features["response"]["result"])

for item in client.iter_data_feature_items(
    service.service_id,
    attr_filter="emd_cd:=:11650108",
    geometry=False,
    size=1000,
    max_pages=3,
):
    print(item)
```

응답을 직접 다루는 코드에서는 `response_items()`와 `response_page_info()`로
VWorld의 `response.result.items`, `response.page`, `response.record` 구조를
일관되게 읽을 수 있습니다. 로그나 캐시 키에는 `sanitize_request_params()`와
`make_cache_key()`를 쓰면 `key=` 값이 섞이지 않습니다.

WMS/WFS:

```python
image = client.wms_get_map(
    layers=["lp_pa_cbnd_bonbun", "lp_pa_cbnd_bubun"],
    styles=["lp_pa_cbnd_bonbun_line", "lp_pa_cbnd_bubun_line"],
    bbox=(14133818.022824, 4520485.8511757, 14134123.770937, 4520791.5992888),
    width=256,
    height=256,
)
print(image.content_type, len(image.content))

gml = client.wfs_get_feature(
    "lt_c_uq111",
    bbox=(13987670, 3912271, 14359383, 4642932),
    property_name=["mnum", "sido_cd", "sigungu_cd", "ag_geom"],
    max_features=40,
)
print(gml.text[:200])
```

타일 URL:

```python
url = client.wmts_tile_url("Base", 11, 793, 1746)
print(url)
# https://api.vworld.kr/req/wmts/1.0.0/{key}/Base/11/793/1746.png
```

## 개발 검증

```bash
python -m compileall src/vworld tests
python -m pytest
python -m ruff check .
python -m mypy src/vworld
```

자세한 테스트 기준은 [docs/testing.md](docs/testing.md)를 참고하세요.
