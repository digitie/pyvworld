# pyvworld

VWorld(브이월드) HTTP API를 Python에서 쓰기 쉽게 감싼 비공식 클라이언트입니다.

이 패키지는 VWorld 공식 [API 레퍼런스](https://www.vworld.kr/dev/v4apiRefer.do)를 기준으로, Python에서 직접 호출 가능한 REST/OGC/타일 엔드포인트를 함수로 제공합니다. 1.0과 2.0 문서가 함께 있는 API는 2.0만 구현했습니다.

## 특징

- 검색 API 2.0: 장소, 주소, 행정구역, 도로명 검색
- Geocoder API 2.0: 주소 좌표 변환, 좌표 주소 변환
- 2D데이터 API 2.0: `GetFeature`, `GetFeatureType`, 공식 서비스 ID 158건 카탈로그
- WMS/WFS API 2.0 레퍼런스: `GetCapabilities`, `GetMap`, `GetFeatureInfo`, `DescribeFeatureType`, `GetFeature`
- 범례이미지/StaticMap API 2.0: 이미지 바이트 응답과 URL 빌더
- WMTS/TMS: 타일, 해외위성영상 테마 타일, capabilities/resource URL
- 네트워크 없이 검증되는 fixture/mock 기반 테스트

JS 지도 SDK, WebGL 3D 지도 SDK, 모바일/데스크톱 SDK는 Python HTTP 엔드포인트가 아니라 런타임 SDK 문서이므로 이 패키지의 함수 래핑 범위에서 제외했습니다. 범위와 근거는 [docs/api-coverage.md](docs/api-coverage.md)에 정리했습니다.

## 설치

```bash
pip install pyvworld
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

도메인 파라미터가 필요한 환경에서는 `VWORLD_DOMAIN` 또는 클라이언트 생성자의 `domain=`을 사용합니다.

## 사용 예시

```python
from pyvworld import VworldClient

client = VworldClient.from_env()

result = client.search_address("성남시 분당구 판교로 242")
print(result["response"]["result"]["items"])

coord = client.geocode("판교로 242", type="road")
print(coord["response"]["result"]["point"])

reverse = client.reverse_geocode((127.101313354, 37.402352535), type="both")
print(reverse["response"]["result"])
```

2D 데이터 API:

```python
from pyvworld import VworldClient, get_data_service

client = VworldClient.from_env(domain="example.com")
service = get_data_service("LT_C_ADEMD_INFO")

features = client.get_data_feature(
    service.service_id,
    attr_filter="emd_cd:=:11650108",
    geometry=False,
    columns=["emd_cd", "full_nm"],
)
print(features["response"]["result"])
```

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
python -m compileall pyvworld tests
python -m pytest
python -m ruff check .
python -m mypy pyvworld
```

자세한 테스트 기준은 [docs/testing.md](docs/testing.md)를 참고하세요.
