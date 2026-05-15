# vworld-debug-ui

`python-vworld-api`를 라이브로 호출해 입력, 요청, 원본 응답, Pydantic 파싱 결과, 처리 결과를 확인하고 fixture JSON으로 저장하는 Streamlit 웹툴입니다.

## 개발 실행

```powershell
cd debug-ui
pip install -e "..[dev]"
pip install -e .
streamlit run app.py
```

저장된 fixture는 루트 프로젝트의 `tests/fixtures/{function}/{case}.json`에 생성됩니다. 기본 pytest는 fixture의 raw response를 replay하므로 VWorld 네트워크를 호출하지 않습니다.
