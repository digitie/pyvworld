---
name: vworld-builder
description: VWorld REST, OGC, image, WMTS, TMS API용 `vworld` Python client를 구현, 확장, test, 문서화할 때 사용한다.
---

# vworld Builder — 에이전트 매뉴얼

> 이 파일은 당신(AI 에이전트)이 작업을 시작하기 전 반드시 읽어야 한다.

## 1. 정체성

이 저장소(GitHub 이름 `python-vworld-api`, Python 패키지 `vworld`)는 VWorld REST, OGC, 정적 이미지, WMTS/TMS API를 래핑하는 비공식 Python 클라이언트다. `VworldClient`(동기)와 `AsyncVworldClient`(비동기)를 제공한다.

## 2. 먼저 읽을 것

1. `README.md` — 프로젝트 개요와 빠른 시작
2. `vworld-api.md` — VWorld API 공식 참조 정리
3. `docs/resume.md` — 현재 진척도와 "다음 한 작업"
4. `docs/api-coverage.md` — 구현 범위
5. `docs/repeated-mistakes.md` — 반복 실수

## 3. 디렉토리 지도

```
src/vworld/
  client.py      # VworldClient, AsyncVworldClient 진입점
  _http.py       # HTTP helper, 오류-예외 매핑
  _params.py     # 파라미터 정규화, 검증
  models.py      # 공개 Pydantic v2 모델, enum
  catalog.py     # 공식 158-entry API 카탈로그
  parser.py      # VWorld JSON → Pydantic 파싱
  processor.py   # 파싱 결과 → 공통 비교 형태 정규화
  debug.py       # fixture 생성용 디버그 실행기
  metadata.py    # 응답 메타데이터, 민감정보 제거
  pagination.py  # 페이지네이션 헬퍼
  exceptions.py  # 예외 계층

debug-ui/          # Streamlit 디버그 UI (별도 패키지)
tests/             # offline 테스트 + live smoke 테스트
docs/              # 프로젝트 문서
```

## 4. 불변 조건

- Search, Geocoder, 2D Data, Legend, StaticMap은 VWorld API 2.0만 사용한다.
- WMS/WFS OGC protocol version은 VWorld API 1.0이 아니다.
- WMTS/TMS는 query parameter가 아니라 path에 key를 둔다.
- 기본 test는 offline이어야 한다.
- Error mapping은 `src/vworld/_http.py`가 소유한다.
- Sync/Async validation·param 로직은 `_make_*_params()` 공유 함수를 사용한다.
- fixture/history 저장 전 `redact_sensitive()`로 모든 필드를 마스킹한다.

## 5. 절대 하지 말 것 (DO NOT)

`AGENTS.md` §절대 하지 말 것과 동일하지만 핵심만 다시 적는다:

1. API key 평문 커밋 금지.
2. Sync/Async 로직 분기 금지 — `_make_*_params()` 공유 함수 사용.
3. 단순 전달용 wrapper 금지.
4. HTTP 오류 매핑 분산 금지 — `_http.py`에만 둔다.
5. 1.0 API 구현 금지.
6. 기본 테스트에서 라이브 네트워크 호출 금지.
7. 문서에 절대 경로 금지.

## 6. 자주 묻는 작업

| 작업 | 시작 파일 |
|------|-----------|
| 새 엔드포인트 추가 | `src/vworld/client.py` → `tests/test_client_rest.py` |
| 새 데이터 서비스 추가 | `src/vworld/catalog.py` → `tests/test_catalog.py` |
| 에러 매핑 추가 | `src/vworld/_http.py` → `tests/test_http.py` |
| 디버그 함수 추가 | `src/vworld/debug.py` → `tests/test_debug.py` |
| fixture 포맷 변경 | `debug-ui/vworld_debug_ui/fixture_writer.py` |

## 7. 도메인 어휘

| 용어 | 의미 |
|------|------|
| Search API | 장소/주소/행정동/도로명 검색 (REST 2.0) |
| Geocoder | 주소→좌표(getcoord), 좌표→주소(getaddress) |
| 2D Data | GetFeature, GetFeatureType (공간 데이터 조회) |
| StaticMap | 정적 지도 이미지 생성 |
| WMTS/TMS | 타일 맵 서비스 (path에 key 포함) |
| WMS/WFS | OGC 표준 맵/피처 서비스 |

## 8. 필수 확인

```bash
python -m compileall src/vworld tests
python -m pytest
python -m ruff check .
python -m mypy src/vworld
```

## 9. Endpoint 추가 절차

1. 공식 VWorld page와 version을 확인한다.
2. `_make_*_params()` 공유 함수를 추가한다.
3. `VworldClient`와 `AsyncVworldClient` 양쪽에 method를 추가한다.
4. 정확한 path/query shape를 assert하는 test를 추가한다.
5. 사용자-facing 변경이면 `docs/api-coverage.md`와 README를 갱신한다.
6. 새 gotcha는 `docs/repeated-mistakes.md`에 추가한다.

## 10. 작업 후 체크리스트

- [ ] `python -m pytest` 통과
- [ ] `python -m ruff check .` / `python -m mypy src/vworld` 통과
- [ ] `docs/journal.md`에 작업 항목 추가 (역시간순)
- [ ] `docs/resume.md`의 진척도 갱신
- [ ] 의사결정이 있었다면 `docs/decisions.md`에 ADR 추가
- [ ] 사용자 가시 변경이면 `CHANGELOG.md` 갱신
