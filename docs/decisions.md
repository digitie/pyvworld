# Architecture Decision Records (ADR)

## ADR-001: Sync/Async param 공유 방식

- **상태**: 채택
- **일자**: 2025-05-23
- **맥락**: `VworldClient`와 `AsyncVworldClient`가 validation과 param 조립 로직을 각각 ~900행씩 중복하고 있었다. 한쪽에만 버그 수정이 적용될 위험이 있었다.
- **결정**: 모듈 레벨 `_make_*_params()` 함수로 추출한다. 두 클래스는 params 함수를 호출한 뒤 HTTP 전송만 담당한다. 상속 mixin이나 제네릭 베이스 클래스 대신 단순 함수 추출을 선택했다.
- **근거**: 함수 추출이 가장 안전하고, 타입 시스템과의 충돌이 없으며, 점진적으로 적용할 수 있다.

## ADR-002: fixture 민감정보 마스킹 범위

- **상태**: 채택
- **일자**: 2025-05-23
- **맥락**: fixture_writer가 `input`, `request`, `response` 필드만 `redact_sensitive()`를 적용하고 `parsed`, `processed` 필드는 누락하고 있었다.
- **결정**: 모든 필드(`input`, `request`, `response`, `parsed`, `processed`)에 `redact_sensitive()`를 적용한다. history_store도 동일하게 적용한다.
- **근거**: 파서가 원본 응답 URL을 보존할 수 있으므로 모든 출력에서 마스킹해야 한다.
