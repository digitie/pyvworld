# Debug UI

이 문서는 `rest_api_debug_ui_fixture_testcase_final.docx` 설계안을 현재 `python-vworld-api` 구조에 맞춘 구현 내용을 기록합니다.

## 목표

- REST API 입력값을 빠르게 바꿔 라이브 실행합니다.
- Raw response, Pydantic parsed result, processed result, validation error를 분리해 봅니다.
- 의미 있는 디버깅 케이스를 fixture JSON으로 저장합니다.
- 저장된 fixture를 pytest replay runner가 자동으로 읽어 회귀 테스트에 사용합니다.

## 프로젝트 구조

```text
src/vworld/
  debug.py        # Streamlit에 의존하지 않는 DebugRun 실행기
  parser.py       # VWorld JSON 응답을 Pydantic v2 모델로 파싱
  processor.py    # replay 비교에 쓰기 좋은 공통 결과로 정규화

debug-ui/
  pyproject.toml
  app.py
  vworld_debug_ui/
    __init__.py
    fixture_writer.py
    history_store.py
    preset_store.py

tests/
  fixtures/
  runners.py
  utils.py
  test_generated_fixtures.py
```

루트 라이브러리는 Streamlit에 의존하지 않습니다. `debug-ui`가 editable 또는 wheel로 설치된 `python-vworld-api`를 import해서 사용합니다.

## 실행 방법

```bash
pip install -e ".[dev]"
cd debug-ui
pip install -e .
streamlit run app.py
```

앱에서 API key를 입력하거나 `VWORLD_API_KEY` 환경변수를 사용합니다. `Domain`은 `VWORLD_DOMAIN`을 기본값으로 읽습니다.
프로젝트 루트 `.env`가 있으면 `VWORLD_API_KEY`, `VWORLD_DOMAIN`을 먼저 UI 기본값으로 채웁니다.
서비스키를 복사/붙여넣기하면서 앞뒤 공백, 탭, 줄바꿈이 들어가도 `VworldClient`가 호출 전에 제거합니다.

## 지원 함수

- `search`
- `geocode`
- `reverse_geocode`
- `get_data_feature`

각 함수는 기존 공개 클라이언트 메서드를 호출합니다. 요청/응답 수집은 `src/vworld/debug.py`에서 session wrapper로 처리하며, HTTP 오류와 VWorld body 오류 매핑은 계속 `src/vworld/_http.py`에만 있습니다.

함수 선택 목록과 입력 파라미터는 `src/vworld/catalog.py`의 `list_api_catalog()`에서 가져옵니다. 각 API 카탈로그 항목에는 VWorld 서비스키 발급 링크가 포함되어 UI 사이드바와 Debug Trace 탭에 표시됩니다.

`get_data_feature`의 데이터셋 입력은 공식 2D 데이터 카탈로그를 사용해 `데이터셋명 (서비스ID)` 형태로 표시합니다. 선택된 데이터셋의 카테고리, 제공기관, 갱신일도 UI와 Debug Trace 탭에서 확인할 수 있습니다.

## Fixture 저장 포맷

기본 저장 위치는 `tests/fixtures/{function}/{case}.json`입니다.

주요 필드:

- `input`: UI 입력값
- `request`: 인증값이 제거된 요청 URL, endpoint, query, headers
- `response`: status code, headers, body
- `parsed`: Pydantic model dump
- `processed`: processor 결과
- `assertion`: replay assertion mode와 제외/필수 필드
- `meta`: 생성 시각, 라이브러리 버전, source

Fixture writer는 `input`, `request`, `response`, `parsed`, `processed` 모든 필드에서 API key, Authorization header, access token, refresh token, VWorld `key` query, WMTS/TMS path key를 저장 전에 마스킹합니다. 같은 fixture 파일명은 기본적으로 덮어쓰지 않습니다.

## Replay 테스트

`tests/test_generated_fixtures.py`는 `tests/fixtures/**/*.json`을 자동으로 읽습니다. 실제 VWorld API를 다시 호출하지 않고 다음 순서로 검증합니다.

```text
fixture response.body
  -> parser
  -> processor
  -> assertion 비교
```

초기 assertion mode는 `snapshot`, `schema_only`, `required_fields`를 지원합니다.
