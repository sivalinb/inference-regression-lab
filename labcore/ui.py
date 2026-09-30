import json
import os
from pathlib import Path
import pandas as pd
import streamlit as st
from labcore.ai import ask
from labcore.sources import catalogue, fetch_source


def header(title, subtitle, config_meta):
    st.set_page_config(page_title=title, page_icon="◈", layout="wide")
    st.markdown("""<style>
    .stApp {background: #09131e;} [data-testid="stHeader"]{background:transparent;}
    h1,h2,h3{letter-spacing:-.035em;} [data-testid="stMetric"]{background:#112331;border:1px solid #244557;border-radius:12px;padding:18px;}
    .eyebrow{color:#66e0c2;font-family:monospace;font-size:12px;letter-spacing:3px;margin-top:12px;}
    </style>""", unsafe_allow_html=True)
    st.markdown('<div class="eyebrow">INFRASTRUCTURE / EXPERIMENT WORKBENCH</div>', unsafe_allow_html=True)
    st.title(title)
    st.write(subtitle)
    st.sidebar.caption("CONFIGURATION")
    st.sidebar.write(config_meta["mode"])
    st.sidebar.code(config_meta["sha256"][:16])
    st.sidebar.caption("Reports and JSONL audit events are saved under artifacts/. Inputs and API keys are not logged.")


def evidence(report):
    if not report:
        st.info("Run an experiment to create an evidence report.")
        return
    st.caption("Evidence mode: " + report.get("mode", "unspecified"))
    st.download_button("Download evidence JSON", json.dumps(report, indent=2), "evidence.json", "application/json")
    with st.expander("Full evidence and configuration"):
        st.json(report)


def sources_panel(root):
    sources = catalogue(root)
    st.write("Public inputs are explicitly attributed. Fetching is optional; the built-in scenarios remain available offline.")
    st.dataframe(pd.DataFrame([{k: s[k] for k in ("id", "title", "license", "purpose")} for s in sources]), hide_index=True)
    selected = st.selectbox("Public source", [s["id"] for s in sources], key="public_source")
    item = next(s for s in sources if s["id"] == selected)
    st.markdown(f"[Open upstream source]({item['url']})")
    if st.button("Fetch public source", key="fetch_source"):
        try:
            result = fetch_source(root, selected)
            st.session_state["source_result"] = result
            st.success("Downloaded with a content hash and provenance record.")
        except Exception as e:
            st.error(f"Download failed: {type(e).__name__}: {e}")
    if "source_result" in st.session_state:
        result = st.session_state["source_result"]
        st.json(result)
        st.download_button("Download source data", Path(result["local_path"]).read_bytes(), result["source_id"] if "source_id" in result else result["id"] + ".data")


def ai_panel(root, report=None):
    documents = json.loads((root / "data/knowledge.json").read_text())
    st.write("Retrieve cited engineering guidance locally, or explicitly send a question and experiment report to a configured model.")
    question = st.text_input("Ask about the experiment", "How should I interpret a failed experiment?")
    use_model = st.checkbox("Use a model endpoint", value=False)
    endpoint = model = None
    if use_model:
        endpoint = st.text_input("Chat API base URL", os.environ.get("LAB_MODEL_BASE_URL", "http://127.0.0.1:8080/v1"))
        model = st.text_input("Model name", os.environ.get("LAB_MODEL", "local"))
        st.caption("Only clicking Answer sends the question, retrieved evidence, and current report to this endpoint. Keys come from LAB_MODEL_API_KEY.")
    if st.button("Answer", key="answer"):
        try:
            result = ask(question, documents, endpoint=endpoint, model=model or "", evidence=report)
            st.caption(result["mode"])
            st.write(result["answer"])
            for source in result["citations"]:
                st.markdown(f"[{source['id']}: {source['title']}]({source['url']})")
        except Exception as e:
            st.error(f"Model request failed ({type(e).__name__}). Local retrieval remains available.")


def docs_panel(root):
    selected = st.selectbox("Guide", [p.name for p in sorted((root / "docs").glob("*.md"))])
    st.markdown((root / "docs" / selected).read_text())
