# 코드 리뷰 보고서 (2025-05-23)

전체 코드베이스에 대한 정적 리뷰 결과를 정리한다.

## 요약

| 심각도 | 건수 | 핵심 내용 |
|--------|------|-----------|
| Critical | 2 | fixture 마스킹 누락, HttpxMock 미소비 라우트 미검증 |
| Major | 10 | AsyncVworldClient 테스트 부재, Sync/Async 코드 중복, 문서-구현 불일치 등 |
| Minor | 27 | 타입 안전성, 성능, 문서 일관성 등 |
| Suggestion | 17 | 구조 개선, UX 개선 등 |

**긍정적인 측면:**
- 예외 계층 구조가 잘 설계되어 있다 (`VworldError` 기반 Auth, RateLimit, InvalidParameter, NoData, Server, Network 에러 분리).
- 인증 정보 보호 메커니즘이 충실하다 (`sanitize_request_params`, `redact_credentials_in_text` 등).
- 좌표, bbox, 줌 레벨, 페이지 크기 등에 대한 유효성 검사가 요청 전에 수행된다.
- Pydantic v2의 불변 모델, 필드 검사기 등을 적절히 활용한다.
- 페이지네이션 무한 루프 방지 가드(`max_pages`, `max_items`)가 있다.
- 동기 클라이언트의 테스트 품질이 우수하다.

---

## Critical

### C-1. fixture의 `parsed`/`processed` 필드에 `redact_sensitive()` 미적용

- **파일**: `debug-ui/vworld_debug_ui/fixture_writer.py` 109-110행
- `input`, `request`, `response` 필드에는 `redact_sensitive()`를 적용하지만, `parsed`와 `processed` 필드에는 적용하지 않는다.
- 파서나 프로세서가 원본 응답에서 API 키가 포함된 URL을 보존하면 fixture 파일에 민감 정보가 노출될 수 있다.
- `docs/debug-ui.md` 77행과 `docs/testing.md` 56행에서 "저장 전에 마스킹합니다"라고 문서화하고 있으나, 실제 구현에서는 `parsed`와 `processed`에 대한 마스킹이 누락되어 있다.

### C-2. HttpxMock에 미소비 라우트 검증(assert_all_called) 부재

- **파일**: `tests/conftest.py` 62-68행
- `routes.pop(index)`은 매칭된 라우트를 소비하지만, teardown 시 `assert len(http_mock.routes) == 0` 같은 검증이 없다.
- 테스트가 예상보다 적은 HTTP 호출을 하거나 로직이 잘못되어도 통과할 수 있다.

---

## Major

### M-1. AsyncVworldClient의 대부분 메서드 테스트 부재

- **파일**: `tests/test_async_client.py`
- `search_place`, `geocode`, `get_data_feature`, `static_map`, `get_wmts_tile` 정도만 커버한다.
- 테스트되지 않는 메서드: `search_address`, `search_district`, `search_road`, `get_coord`, `reverse_geocode_latlon`, `get_data_feature_type`, `wms_get_map`, `wms_get_feature_info`, `wfs_get_feature`, `wfs_get_capabilities`, `wfs_describe_feature_type`, `get_legend_graphic`, `get_legend_style`, `static_map_latlon`, `get_wmts_capabilities`, `get_tms_resource`, `get_tms_tile`, `get_wmts_theme_tile`, `get_tms_theme_tile`, `from_env_file` 등

### M-2. VworldClient와 AsyncVworldClient 간 로직 중복 (DRY 위반)

- **파일**: `src/vworld/client.py`
- 두 클래스의 validation 로직, parameter 구성 로직이 거의 동일하게 중복되어 있다 (약 900행).
- 한쪽에만 버그 수정이 적용될 위험이 있다.
- `_wms_get_map_params`, `_legend_params`, `_static_map_params` 등을 공유 모듈로 추출하면 유지보수가 크게 개선된다.

### M-3. `iter_data_feature_items` 이터레이터 테스트 부재

- **파일**: `src/vworld/client.py` 510-552행
- `iter_data_feature_items`는 테스트가 전혀 없다.

### M-4. 문서의 마스킹 범위가 실제 구현보다 넓다

- **파일**: `docs/debug-ui.md` 76-77행, `docs/testing.md` 56행
- "저장 전에 마스킹합니다"라고 기술하지만 `parsed`/`processed` 필드는 마스킹되지 않는다 (C-1과 연관).

### M-5. History에 입력값 마스킹 미적용

- **파일**: `debug-ui/vworld_debug_ui/history_store.py` 26-28행
- `debug_run.input`을 `redact_sensitive()` 없이 그대로 저장한다.
- `fixture_writer.py`에서 `redact_sensitive()`를 적용하는 것과 일관성이 없다.

### M-6. API 키 URL 노출 경고 부재

- **파일**: `src/vworld/client.py`
- `*_url()` 메서드가 API 키를 포함한 URL을 반환하지만, 로깅이나 사용자 UI에 노출될 수 있다는 경고가 없다.

### M-7. `_required_text` 의미 혼란

- **파일**: `src/vworld/client.py`
- `_required_text` 검증의 의미가 메서드마다 다르게 사용되어 코드 읽기가 어렵다.

### M-8. debug 함수 테스트 부재

- **파일**: `src/vworld/debug.py` 92-105행, 121-129행, 134-144행
- `run_debug_function()`, `debug_geocode()`, `debug_reverse_geocode()`에 대한 테스트가 없다.

### M-9. parser 직접 테스트 부재

- **파일**: `src/vworld/parser.py` 31-46행
- `parse_geocode_response`, `parse_reverse_geocode_response`, `parse_data_feature_response`는 fixture runner를 통해 간접적으로만 테스트된다. 현재 fixture는 `search` 한 건뿐이므로 이 파서들의 fixture 기반 테스트가 없다.

### M-10. Debug UI `current_input` 탭 간 에러 전파 누락

- **파일**: `debug-ui/app.py` 134-136행
- `_raw_response_tab`이 예외를 발생시키면 `current_input`이 빈 딕셔너리로 남아 Debug Trace 탭에서 데이터가 표시되지 않지만, 사용자에게 별도 에러 피드백이 없다.

---

## Minor

### 코어 라이브러리

- **env 파일 권한 미검증**: `.env` 파일 읽기 시 파일 권한을 검사하지 않는다.
- **내장 이름 섀도잉**: 일부 변수가 Python 내장 이름을 가린다.
- **재시도 로직**: `_AsyncVworldHttp._get()`의 재시도/에러 경로가 비동기 측에서 테스트되지 않는다 (`src/vworld/_http.py` 185-214행).
- **`VworldClient.close()`와 컨텍스트 매니저 테스트 부재** (`src/vworld/client.py` 178-188행).
- **`processor.py` 에러 케이스 미테스트**: `root`가 `Mapping`이 아닌 경우 경로 (`src/vworld/processor.py` 28-46행).
- **`metadata.py` 일부 경로 미테스트**: `time` 객체, `Enum`, `set`, `frozenset` 입력 변환 (`src/vworld/metadata.py` 127-141행).

### 테스트

- **Python 3.14 classifier**: `pyproject.toml` 26행에 포함되어 있으나 CI 검증 여부 미확인.
- **`test_pagination.py` 조건부 assertion 불안정**: `"result" in str(payload)` 조건이 fragile하다 (93-98행).
- **Fixture 데이터가 `search` 한 건뿐**: `geocode`, `reverse_geocode`, `get_data_feature`에 대한 fixture가 없다.
- **`test_live_api.py`에서 `.env` 파싱 로직 중복**: `_local_env()`가 `client.py`의 `_read_env_file()`과 거의 동일하다 (19-29행).

### Debug UI

- **`load_presets` 이중 호출**: `_sidebar()`와 `_request_form()`에서 각각 호출한다 (`app.py` 75, 201행).
- **`Environment` 셀렉트박스가 기능 없음**: 선택값이 캡션 표시 외에 사용되지 않는다 (`app.py` 81행).
- **`unsafe_allow_html=True`로 CSS 삽입**: 현재는 정적 CSS만이므로 위험은 낮다 (`app.py` 619-640행).
- **동일 초에 같은 함수 실행 시 history 파일 덮어쓰기** (`history_store.py` 22-23행).

### 문서

- **CHANGELOG.md가 영어**: AGENTS.md의 한글 작성 규칙에 위반된다.
- **`debug-ui/pyproject.toml`의 `__init__.py`가 프로젝트 구조 다이어그램에 누락** (`docs/debug-ui.md` 14-33행).
- **WSL_KRADDR_GEO_DEBUG_UI.md에 절대 경로 사용**: AGENTS.md 40행의 상대 경로 규칙에 위반된다.
- **README에서 `get_data_feature_type`을 언급하지만 debug UI에서는 미지원**이라는 차이가 명시되지 않았다.

---

## Suggestion

### 구조 개선

- 카탈로그 데이터를 별도 파일로 분리한다.
- 파서/프로세서 확장점을 문서화한다.
- connection pool 설정을 노출한다.
- `__all__`을 필요한 것만 포함하도록 축소한다.
- `_query()` 헬퍼와 `BASE` URL 상수를 테스트 간 공유한다 (4-7개 파일에 중복).
- `ok_payload` fixture에 pagination 메타데이터를 포함한다.
- `pytest-asyncio`를 도입하여 비동기 테스트를 관용적으로 작성한다.
- `pyproject.toml`에 `project.urls`와 작성자 email을 추가한다.

### UX 개선

- History 패널에서 기록 클릭으로 입력값을 폼에 채우는 재실행 기능을 추가한다.
- Fixture 저장 시 description 기본값을 함수명+시간으로 제안한다.
- Timeout 오류 발생 시 안내 메시지를 표시한다.
- `slugify`에서 한글 자모(ㄱ-ㅎ, ㅏ-ㅣ)도 허용한다.
- URL 쿼리 파라미터 redaction 정규식에 `access_token`, `refresh_token`도 포함한다.

---

## 권장 우선순위

1. **즉시 수정**: C-1 (fixture 마스킹 누락) — 민감 정보 노출 위험
2. **즉시 수정**: M-5 (history 마스킹 누락) — 위와 동일한 위험
3. **단기**: M-2 (Sync/Async 코드 중복 해소) — 유지보수 비용 절감
4. **단기**: C-2, M-1 (테스트 인프라 강화) — 회귀 방지
5. **중기**: 나머지 Major 항목 해결
6. **장기**: Minor, Suggestion 항목 점진적 개선
