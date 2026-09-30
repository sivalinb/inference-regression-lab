from pathlib import Path
import json
import pandas as pd
import streamlit as st
from labcore.config import load_config
from labcore.observability import Recorder
from labcore.runtime import AppleContainer
from labcore.ui import header,evidence,sources_panel,ai_panel,docs_panel
from engine import run_benchmark,compare,gsm8k_prompts,start_server,stop_server,stream_request,PROMPTS

ROOT=Path(__file__).resolve().parent
config,meta=load_config(ROOT)
header("Inference Regression Lab","Inspect streaming latency, throughput, quality, and regressions together.",meta)

@st.cache_resource
def recorder(): return Recorder(ROOT,"inference-regression-lab")

tabs=st.tabs(["Benchmark","Model server","Baseline","Evidence","AI reviewer","Public sources","Guide"])
with tabs[0]:
    mode=st.radio("Execution mode",["Protocol replay","Live model endpoint"],horizontal=True)
    server=st.session_state.get("server",{})
    endpoint=st.text_input("Chat API base URL",server.get("endpoint","http://127.0.0.1:8080/v1"))
    model=st.text_input("Model identifier",server.get("model","local"))
    a,b,c=st.columns(3)
    config["requests"]=a.number_input("Requests",2,100,config["requests"])
    config["concurrency"]=b.number_input("Concurrency",1,8,config["concurrency"])
    config["maxTokens"]=c.number_input("Maximum tokens",1,512,config["maxTokens"])
    use_public=st.checkbox("Use fetched GSM8K questions")
    if st.button("Run benchmark",type="primary"):
        try:
            prompts=None
            if use_public:
                source=st.session_state.get("source_result")
                if not source or source["id"]!="gsm8k": raise ValueError("Fetch GSM8K in Public sources first")
                prompts=gsm8k_prompts(source["local_path"])
            with recorder().span("inference_benchmark",mode=mode):
                report=run_benchmark(config,endpoint if mode=="Live model endpoint" else None,model,prompts)
                report["config_provenance"]=meta
                recorder().save(report)
                st.session_state["report"]=report
        except Exception as e: st.error(str(e))
    if "report" in st.session_state:
        report=st.session_state["report"]
        s=report["summary"]
        a,b,c,d=st.columns(4)
        a.metric("p95 TTFT",f'{s["p95_ttft_ms"]:.0f} ms' if s["p95_ttft_ms"] is not None else "Unavailable")
        b.metric("Errors",f'{s["error_rate"]:.1%}')
        c.metric("Tokens / second",f'{s["aggregate_tokens_per_second"]:.1f}' if s["aggregate_tokens_per_second"] is not None else "Not reported")
        d.metric("SLO gate","PASS" if s["slo_passed"] else "FAIL")
        st.caption(report["mode"]+" · "+s["sample_note"])
        frame=pd.DataFrame(report["rows"])
        st.line_chart(frame[["ttft_ms","duration_ms"]])
        st.dataframe(frame.drop(columns=["chunk_arrival_seconds"],errors="ignore"),hide_index=True)
    if st.button("Test client cancellation after two chunks",disabled=mode!="Live model endpoint"):
        result=stream_request(endpoint,model,PROMPTS[2],config,cancel_after=2)
        st.json(result)
        st.caption("This measures client stream closure. It does not prove server-side compute reclamation.")
with tabs[1]:
    st.write("Launch CPU inference in Apple Container. The selected GGUF file is staged in a private temporary directory and mounted read-only.")
    cached_model=ROOT/"artifacts/models/SmolLM2-135M-Instruct-Q4_K_M.gguf"
    model_path=st.text_input("GGUF model path",str(cached_model) if cached_model.exists() else "")
    if st.button("Start isolated model server"):
        try:
            if st.session_state.get("server"): raise ValueError("Stop the current server first")
            st.session_state["server"]=start_server(model_path,config["cpus"],config["memoryMb"])
            st.success("Server ready. Switch to Benchmark.")
        except Exception as e: st.error(str(e))
    if st.session_state.get("server"):
        st.json(st.session_state["server"])
        if st.button("Stop this model server"):
            stop_server(st.session_state["server"])
            del st.session_state["server"]
            st.success("Server removed")
with tabs[2]:
    if st.button("Save current report as session baseline") and "report" in st.session_state:
        st.session_state["baseline"]=st.session_state["report"]
    baseline_file=st.file_uploader("Or upload a baseline report",type=["json"])
    if st.button("Compare current report"):
        try:
            baseline=json.loads(baseline_file.getvalue()) if baseline_file else st.session_state["baseline"]
            st.json(compare(baseline,st.session_state["report"]))
        except Exception as e: st.error(str(e))
with tabs[3]: evidence(st.session_state.get("report"))
with tabs[4]: ai_panel(ROOT,st.session_state.get("report"))
with tabs[5]: sources_panel(ROOT)
with tabs[6]: docs_panel(ROOT)
