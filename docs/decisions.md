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

## ADR-003: 외부 주소 DTO 비의존

- **상태**: 채택
- **일자**: 2026-05-28
- **맥락**: `python-kraddr-base`의 `PlaceCoordinate`, `Address` 같은 외부 DTO를 공개 입력으로 받으면 이 패키지가 VWorld HTTP client를 넘어 앱 공통 주소 모델의 호환성까지 떠안게 된다.
- **결정**: `python-kraddr-base`를 런타임 의존성으로 두지 않고, 소스 코드에서도 해당 DTO를 참조하지 않는다. 공개 함수는 문자열 주소, VWorld `x,y` 문자열, `(lon, lat)` 튜플, 또는 이 패키지의 값 객체만 다룬다.
- **근거**: VWorld 공식 API는 문자열 주소와 `x,y` point만 요구한다. 외부 DTO 변환은 호출자 경계에서 끝내는 편이 요청 조립 책임을 단순하게 유지한다.
