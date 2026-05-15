"""Streamlit 기반 VWorld REST 디버그 UI."""
# ruff: noqa: E402

from __future__ import annotations

import sys
from importlib import metadata
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if SRC_DIR.exists():
    sys.path.insert(0, str(SRC_DIR))

import pandas as pd
import streamlit as st
from vworld_debug_ui.fixture_writer import jsonable, save_fixture
from vworld_debug_ui.history_store import append_history, load_recent_history
from vworld_debug_ui.preset_store import load_presets, save_preset

from vworld import (
    DATA_SERVICES,
    ApiCatalogEntry,
    ApiParameter,
    VworldClient,
    data_service_label,
    list_api_catalog,
    run_debug_function,
)
from vworld.debug import DebugRun

FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures"
DATA_DIR = Path(__file__).resolve().parent / "data"
API_CATALOG = list_api_catalog()
CATALOG_BY_FUNCTION = {entry.function: entry for entry in API_CATALOG}


def main() -> None:
    st.set_page_config(page_title="VWorld REST Debug UI", layout="wide")
    _style()

    st.title("VWorld REST Debug UI")
    st.caption("라이브 호출 결과를 확인하고 fixture JSON으로 저장합니다.")

    selected_entry, api_key, domain, timeout, preset_name = _sidebar()
    current_input = _input_panel(selected_entry, preset_name)
    client = VworldClient(
        api_key=api_key or None,
        domain=domain,
        timeout=timeout,
        retry_backoff=0,
    )

    main_col, history_col = st.columns([0.74, 0.26], gap="large")
    with main_col:
        run_clicked = st.button("Run", type="primary", use_container_width=True)
        if run_clicked:
            debug_run = run_debug_function(client, selected_entry.function, current_input)
            st.session_state["last_run"] = debug_run
            append_history(DATA_DIR / "history", debug_run)

        debug_run = st.session_state.get("last_run")
        if isinstance(debug_run, DebugRun):
            _result_tabs(debug_run)
        else:
            st.info("입력값을 확인한 뒤 Run을 누르면 결과 탭이 열립니다.")

    with history_col:
        _history_panel()


def _sidebar() -> tuple[ApiCatalogEntry, str, str | None, float, str]:
    st.sidebar.header("Run settings")
    selected_function = st.sidebar.selectbox(
        "Function",
        options=tuple(CATALOG_BY_FUNCTION),
        format_func=lambda name: CATALOG_BY_FUNCTION[name].label,
    )
    selected_entry = CATALOG_BY_FUNCTION[selected_function]
    st.sidebar.caption(selected_entry.description)
    st.sidebar.link_button(
        "서비스키 발급받기",
        selected_entry.auth_key_url,
        use_container_width=True,
    )
    presets = load_presets(DATA_DIR / "presets", selected_function)
    preset_names = ["Default", *sorted(presets)]
    preset_name = st.sidebar.selectbox("Preset", preset_names)
    environment = st.sidebar.selectbox("Environment", ("local", "release-wheel"))
    st.sidebar.caption(f"Environment: {environment}")
    default_key, default_domain = _default_client_settings()
    api_key = st.sidebar.text_input(
        "API key",
        value=default_key,
        type="password",
        help=(
            "프로젝트 .env 또는 VWORLD_API_KEY를 기본값으로 읽습니다. "
            "복붙 공백은 호출 시 제거됩니다."
        ),
    )
    domain = st.sidebar.text_input("Domain", value=default_domain)
    timeout = st.sidebar.number_input("Timeout seconds", min_value=1.0, value=10.0, step=1.0)
    return selected_entry, api_key, domain, float(timeout), preset_name


def _input_panel(entry: ApiCatalogEntry, preset_name: str) -> dict[str, Any]:
    presets = load_presets(DATA_DIR / "presets", entry.function)
    preset = presets.get(preset_name, {}) if preset_name != "Default" else {}
    values: dict[str, Any] = {}

    st.subheader("Input parameters")
    with st.container(border=True):
        columns = st.columns(2)
        for index, field in enumerate(entry.parameters):
            target = columns[index % 2]
            default = preset.get(field.name, field.default)
            with target:
                values[field.name] = _field_widget(field, default)
        save_name = st.text_input("Preset name", value="", key=f"preset-name-{entry.function}")
        save_clicked = st.button("Save preset", key=f"save-preset-{entry.function}")
        if save_clicked and save_name.strip():
            save_preset(DATA_DIR / "presets", entry.function, save_name, values)
            st.success(f"Preset saved: {save_name}")
    return values


def _field_widget(field: ApiParameter, default: Any) -> Any:
    help_text = field.description or None
    if field.kind == "data_service":
        return _data_service_widget(field, default)
    if field.kind == "select":
        index = field.choices.index(str(default)) if str(default) in field.choices else 0
        return st.selectbox(field.label, field.choices, index=index, help=help_text)
    if field.kind == "checkbox":
        return st.checkbox(field.label, value=bool(default), help=help_text)
    if field.kind == "number":
        return st.number_input(field.label, value=int(default), step=1, help=help_text)
    return st.text_input(
        field.label,
        value="" if default is None else str(default),
        help=help_text,
    )


def _data_service_widget(field: ApiParameter, default: Any) -> str:
    default_id = str(default or field.default).upper()
    selected_index = 0
    for index, service in enumerate(DATA_SERVICES):
        if service.service_id.upper() == default_id:
            selected_index = index
            break
    selected = st.selectbox(
        field.label,
        DATA_SERVICES,
        index=selected_index,
        format_func=data_service_label,
        help=field.description or None,
    )
    st.caption(f"{selected.category} · {selected.provider} · updated {selected.updated_at}")
    return selected.service_id


def _result_tabs(debug_run: DebugRun) -> None:
    raw_tab, parsed_tab, processed_tab, error_tab, trace_tab, fixture_tab = st.tabs(
        [
            "Raw Response",
            "Pydantic Model",
            "Processed Result",
            "Validation Errors",
            "Debug Trace",
            "Fixture / Testcase",
        ]
    )
    with raw_tab:
        st.json(debug_run.response.get("body", debug_run.response), expanded=2)
        st.caption("Request")
        st.json(debug_run.request, expanded=1)
    with parsed_tab:
        _show_json(jsonable(debug_run.parsed), expanded=2)
    with processed_tab:
        processed = jsonable(debug_run.processed)
        _show_json(processed, expanded=2)
        items = processed.get("items", []) if isinstance(processed, dict) else []
        if items:
            st.dataframe(pd.json_normalize(items, sep="."), use_container_width=True)
    with error_tab:
        if debug_run.error:
            st.error(debug_run.error.get("message", "Error"))
            st.json(debug_run.error, expanded=1)
        else:
            st.success("No validation error or exception captured.")
    with trace_tab:
        _catalog_panel(debug_run)
        for entry in debug_run.trace:
            st.write(f"- {entry}")
    with fixture_tab:
        _fixture_panel(debug_run)


def _fixture_panel(debug_run: DebugRun) -> None:
    st.subheader("Save as fixture")
    with st.form(f"fixture-{debug_run.function}"):
        case_name = st.text_input("Case name", value=f"{debug_run.function}_normal")
        description = st.text_area("Description", value="")
        assertion_mode = st.selectbox(
            "Assertion mode",
            ("snapshot", "schema_only", "required_fields"),
        )
        exclude_fields_raw = st.text_input(
            "Exclude fields",
            value="fetched_at, request_id, updated_at",
        )
        required_fields_raw = st.text_input("Required fields", value="")
        overwrite = st.checkbox("Overwrite existing fixture", value=False)
        preview = st.checkbox("Show fixture preview", value=True)
        save_clicked = st.form_submit_button("Save as fixture", type="primary")

    assertion = {
        "mode": assertion_mode,
        "exclude_fields": _csv_values(exclude_fields_raw),
        "required_fields": _csv_values(required_fields_raw),
    }
    if preview:
        st.json(
            {
                "name": case_name,
                "function": debug_run.function,
                "input": debug_run.input,
                "request": debug_run.request,
                "response": debug_run.response,
                "processed": jsonable(debug_run.processed),
                "assertion": assertion,
            },
            expanded=1,
        )
    if save_clicked:
        try:
            path = save_fixture(
                base_dir=FIXTURE_DIR,
                function_name=debug_run.function,
                case_name=case_name,
                description=description,
                input_data=debug_run.input,
                request_data=debug_run.request,
                response_data=debug_run.response,
                parsed_result=debug_run.parsed,
                processed_result=debug_run.processed,
                assertion=assertion,
                library_version=_library_version(),
                overwrite=overwrite,
            )
        except FileExistsError as exc:
            st.error(str(exc))
        else:
            st.success(f"Saved: {path.relative_to(REPO_ROOT)}")


def _history_panel() -> None:
    st.subheader("History")
    rows = load_recent_history(DATA_DIR / "history", limit=8)
    if not rows:
        st.caption("No recent runs.")
        return
    for row in rows:
        status = "OK" if row.get("error") is None else "ERROR"
        function_name = str(row.get("function"))
        catalog = CATALOG_BY_FUNCTION.get(function_name)
        st.markdown(f"**{catalog.label if catalog else function_name}** · {status}")
        st.caption(str(row.get("created_at", "")))


def _catalog_panel(debug_run: DebugRun) -> None:
    if debug_run.catalog is None:
        return
    st.subheader("API catalog")
    st.markdown(f"[서비스키 발급받기]({debug_run.catalog.auth_key_url})")
    st.json(jsonable(debug_run.catalog), expanded=1)
    if debug_run.data_service is not None:
        st.subheader("Dataset catalog")
        st.dataframe(
            pd.DataFrame([jsonable(debug_run.data_service)]),
            use_container_width=True,
            hide_index=True,
        )


def _csv_values(raw: str) -> list[str]:
    return [value.strip() for value in raw.split(",") if value.strip()]


def _show_json(value: Any, *, expanded: int) -> None:
    if value is None:
        st.info("No JSON value to display.")
        return
    st.json(value, expanded=expanded)


def _default_client_settings() -> tuple[str, str]:
    client = VworldClient.from_env_file(REPO_ROOT / ".env", retry_backoff=0)
    return client.api_key or "", client.domain or ""


def _library_version() -> str | None:
    try:
        return metadata.version("python-vworld-api")
    except metadata.PackageNotFoundError:
        return None


def _style() -> None:
    st.markdown(
        """
        <style>
        .stApp { background: #f7f9fc; color: #1e293b; }
        [data-testid="stSidebar"] { background: #ffffff; border-right: 1px solid #e2e8f0; }
        div[data-testid="stForm"] {
          background: #ffffff;
          border: 1px solid #e2e8f0;
          border-radius: 8px;
          padding: 16px;
        }
        .stTabs [data-baseweb="tab-list"] { gap: 4px; }
        .stTabs [data-baseweb="tab"] {
          border-radius: 8px 8px 0 0;
          padding: 8px 12px;
          font-size: 0.9rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
