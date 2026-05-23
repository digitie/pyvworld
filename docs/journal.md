# 작업 기록

역시간순으로 작업 내용을 기록한다.

## 2025-05-23

- 코드 리뷰 보고서 작성 (Critical 2, Major 10, Minor 27, Suggestion 17)
- fixture_writer `parsed`/`processed` 필드에 `redact_sensitive()` 적용 (C-1)
- history_store에 `redact_sensitive()` 적용 + 동일 초 파일 덮어쓰기 방지 (M-5)
- HttpxMock teardown 시 미소비 라우트 검증 추가 (C-2)
- VworldClient/AsyncVworldClient validation·param 로직을 모듈 레벨 `_make_*_params()` 함수로 추출 (M-2)
- AsyncVworldClient 테스트 8건 추가 (search_address, search_district, search_road, reverse_geocode, reverse_geocode_latlon, get_data_feature_type, wms_get_capabilities, wfs_get_feature)
- iter_data_feature_items 테스트 추가 (M-3)
- debug 모듈 테스트 6건 추가 (M-8)
- close/context manager, metadata 변환, HTTP close 테스트 추가
- test_pagination 조건부 assertion을 개별 테스트로 분리
- docs/debug-ui.md, docs/testing.md 마스킹 범위 설명 정정 (M-4)
- pyproject.toml: project.urls 추가, 작성자 email 추가, Python 3.14 classifier 제거
- WSL 문서 절대 경로를 플레이스홀더로 교체
- app.py: 미사용 Environment 셀렉트박스 제거, 탭 간 에러 전파 처리
- fixture_writer URL redaction 패턴에 access_token/refresh_token 추가
- python-kraddr-geo 개발 방식 도입: AGENTS.md 강화, SKILL.md 에이전트 매뉴얼화, resume.md·journal.md·tasks.md·decisions.md 추가, ruff 규칙 확대
