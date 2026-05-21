---
name: vworld-builder
description: VWorld REST, OGC, image, WMTS, TMS API용 `vworld` Python client를 구현, 확장, test, 문서화할 때 사용한다.
---

# vworld Builder

## 문서 언어 정책

이 저장소의 모든 Markdown/RST 문서는 한글로 작성한다. 공식 API field, code identifier, 명령어, URL, provider 원문은 필요한 경우 원문을 유지한다.

## 먼저 읽을 것

1. `vworld-api.md`
2. `docs/api-coverage.md`
3. `docs/repeated-mistakes.md`

## 불변 조건

- Search, Geocoder, 2D Data, Legend, StaticMap은 VWorld API 2.0만 사용한다.
- WMS/WFS OGC protocol version은 VWorld API 1.0이 아니다.
- WMTS/TMS는 query parameter가 아니라 path에 key를 둔다.
- 기본 test는 offline이어야 한다.
- Error mapping은 `src/vworld/_http.py`가 소유한다.

## 필수 확인

```bash
python -m compileall src/vworld tests
python -m pytest
python -m ruff check .
python -m mypy src/vworld
```

## Endpoint 추가

1. 공식 VWorld page와 version을 확인한다.
2. `VworldClient`에 method를 추가한다.
3. HTTP 호출 전에 request parameter를 검증한다.
4. 정확한 path/query shape를 assert하는 test를 추가한다.
5. 사용자-facing 변경이면 `docs/api-coverage.md`와 README를 갱신한다.
6. 새 gotcha는 `docs/repeated-mistakes.md`에 추가한다.
