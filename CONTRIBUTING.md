# 기여 가이드

## 문서 언어 정책

이 저장소의 모든 Markdown/RST 문서는 한글로 작성한다. 공식 API field, code identifier, 명령어, URL, provider 원문은 필요한 경우 원문을 유지한다.

## 개발 환경

```bash
pip install -e ".[dev]"
```

## 확인 명령

Commit 전에 실행한다.

```bash
python -m compileall src/vworld tests
python -m pytest
python -m ruff check .
python -m mypy src/vworld
```

## API 변경

- 공식 VWorld reference page를 먼저 확인한다.
- 1.0과 2.0 문서가 함께 있으면 VWorld 2.0 문서를 우선한다.
- HTTP error mapping은 `src/vworld/_http.py`에 유지한다.
- 정확한 URL/query assertion이 있는 offline test를 추가한다.
- 동작이 바뀌면 `docs/api-coverage.md`와 `docs/repeated-mistakes.md`를 갱신한다.
