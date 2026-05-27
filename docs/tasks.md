# 작업 백로그

## 대기 (우선순위순)

- T-001: fixture 데이터 확보 — `geocode`, `reverse_geocode`, `get_data_feature`에 대한 fixture 추가
- T-002: CI 워크플로우 구성 — GitHub Actions로 pytest, ruff, mypy 자동 검증
- T-003: parser/processor 직접 테스트 추가 — fixture runner 외에 단위 테스트 보강
- T-004: `_http.py` 비동기 재시도/에러 경로 테스트 — `_AsyncVworldHttp._get()` 커버리지

## 완료

- T-005: `python-kraddr-base` 비의존 경계 고정 — 런타임 의존성, 소스 수준 외부 DTO 노출, 편의 함수의 중간 값 객체 생성을 제거. (2026-05-28)

상세 작업 기록은 `docs/journal.md`를 참조한다.
