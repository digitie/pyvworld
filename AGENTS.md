# AGENTS

이 저장소에서 작업할 때 지켜야 할 규칙입니다.

## 작업 환경 규칙

- 이 환경에서 `rg`가 실행 권한 문제로 막히면 `Get-ChildItem -Recurse -File`과 `Select-String`으로 파일 목록/검색을 우회합니다.
- PowerShell로 UTF-8 문서를 읽을 때는 `Get-Content -Encoding UTF8`처럼 인코딩을 명시합니다.

## 구현 원칙

- 공식 VWorld 문서를 먼저 확인합니다.
- 1.0/2.0이 함께 있으면 2.0만 구현합니다.
- REST 계열은 기본 `version=2.0`, `format=json`, `errorformat=json`을 유지합니다.
- HTTP 오류와 VWorld body 오류 매핑은 `pyvworld/_http.py`에만 둡니다.
- 공개 메서드는 파라미터 검증과 URL/요청 조립에 집중합니다.
- SDK 문서(JavaScript, 모바일, 데스크톱)는 HTTP 함수 래핑 대상이 아닙니다.

## 테스트 규칙

- 기본 테스트는 라이브 네트워크를 호출하지 않습니다.
- 새 엔드포인트 메서드를 추가하면 happy path, 잘못된 파라미터, 오류 응답 테스트를 추가합니다.
- URL 경로에 키가 들어가는 WMTS/TMS는 쿼리 `key=`를 붙이지 않는지 반드시 확인합니다.
- 카탈로그를 갱신하면 `len(DATA_SERVICES)` 테스트와 `docs/data-services.md`도 함께 갱신합니다.

## 문서 규칙

- 구현 범위는 `docs/api-coverage.md`에 갱신합니다.
- 반복 실수는 `docs/repeated-mistakes.md`에 남깁니다.
- 사용자 예시는 README에 짧고 실행 가능한 형태로 둡니다.
- 문서에서 파일 위치는 프로젝트 기준 상대 경로로 적고, 로컬 드라이브를 포함한 절대 경로를 남기지 않습니다.
- Python docstring과 주석 같은 내부 문서도 한글로 작성합니다.
