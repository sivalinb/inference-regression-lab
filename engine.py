from concurrent.futures import ThreadPoolExecutor
import hashlib
import ipaddress
import json
import math
import os
from pathlib import Path
import re
import socket
import shutil
import statistics
import tempfile
import time
from urllib.parse import urlparse
import requests
from pydantic import BaseModel, Field
from labcore.runtime import AppleContainer


PROMPTS = [
    {"id":"arithmetic-1","prompt":"What is 17 plus 25? Answer with only the number.","answer":"42"},
    {"id":"arithmetic-2","prompt":"What is 9 multiplied by 8? Answer with only the number.","answer":"72"},
    {"id":"explain-1","prompt":"Explain why a telemetry queue helps during a network outage in two sentences."},
    {"id":"explain-2","prompt":"Explain the difference between latency and throughput in two sentences."},
]


class Experiment(BaseModel):
    requests: int = Field(default=12,ge=2,le=100)
    concurrency: int = Field(default=2,ge=1,le=8)
    maxTokens: int = Field(default=48,ge=1,le=512)
    deadlineSeconds: int = Field(default=30,ge=2,le=120)
    warmupRequests: int = Field(default=1,ge=0,le=5)
    maxP95TtftMs: float = Field(default=5000,gt=0)
    maxErrorRate: float = Field(default=0.05,ge=0,le=1)
    regressionTolerance: float = Field(default=0.2,ge=0,le=1)


def percentile(values, p):
    if not values: return None
    values=sorted(values)
    index=(len(values)-1)*p
    lo,hi=math.floor(index),math.ceil(index)
    return values[lo]+(values[hi]-values[lo])*(index-lo)


def numeric_answer(text):
    target=text.split("####")[-1].strip()
    numbers=re.findall(r"-?\d+(?:\.\d+)?",target.replace(",",""))
    return numbers[-1] if numbers else None


def stream_request(endpoint, model, prompt, config, cancel_after=None):
    c=Experiment.model_validate(config)
    parsed=urlparse(endpoint)
    if parsed.scheme not in {"http","https"} or parsed.username or parsed.password:
        raise ValueError("Invalid endpoint")
    try: private=ipaddress.ip_address(parsed.hostname).is_private
    except ValueError: private=parsed.hostname=="localhost"
    if parsed.scheme=="http" and not private:
        raise ValueError("Remote endpoints require HTTPS")
    headers={}
    if os.environ.get("LAB_MODEL_API_KEY"): headers["Authorization"]="Bearer "+os.environ["LAB_MODEL_API_KEY"]
    started=time.perf_counter()
    first=None
    content=[]
    chunk_times=[]
    tokens=None
    server_model=None
    done=False
    status="ok"
    try:
        session=requests.Session()
        if private: session.trust_env=False
        with session.post(endpoint.rstrip("/")+"/chat/completions",json={"model":model,"messages":[{"role":"user","content":prompt["prompt"]}],
             "temperature":0,"max_tokens":c.maxTokens,"stream":True,"stream_options":{"include_usage":True}},
             headers=headers,stream=True,timeout=(3,c.deadlineSeconds)) as response:
            response.raise_for_status()
            for raw in response.iter_lines(chunk_size=1):
                now=time.perf_counter()
                if now-started>c.deadlineSeconds: raise TimeoutError("Total request deadline")
                if not raw or not raw.startswith(b"data:"): continue
                payload=raw[5:].strip()
                if payload==b"[DONE]":
                    done=True
                    break
                data=json.loads(payload)
                if data.get("error"): raise ValueError("Inference endpoint returned an error event")
                server_model=data.get("model",server_model)
                usage=data.get("usage")
                if usage and usage.get("completion_tokens") is not None: tokens=int(usage["completion_tokens"])
                for choice in data.get("choices",[]):
                    text=choice.get("delta",{}).get("content") or ""
                    if text:
                        if first is None: first=now
                        content.append(text)
                        chunk_times.append(now-started)
                if cancel_after and len(chunk_times)>=cancel_after:
                    status="cancelled"
                    break
        if not done and status!="cancelled": raise ValueError("Stream ended without DONE marker")
        if first is None and status=="ok": raise ValueError("Stream had no generated content")
    except Exception as error:
        status="error"
        error_type=type(error).__name__
    elapsed=time.perf_counter()-started
    text="".join(content)
    result={"prompt_id":prompt["id"],"status":status,"ttft_ms":(first-started)*1000 if first else None,
            "duration_ms":elapsed*1000,"completion_tokens":tokens,"content_chunks":len(content),
            "text":text,"server_model":server_model,"chunk_arrival_seconds":chunk_times,
            "numeric_exact_match":numeric_answer(text)==numeric_answer(prompt["answer"]) if prompt.get("answer") else None}
    if status=="error": result["error_type"]=error_type
    return result


def summarize(rows,wall_seconds,config):
    successful=[r for r in rows if r["status"]=="ok"]
    latencies=[r["ttft_ms"] for r in successful if r["ttft_ms"] is not None]
    errors=sum(r["status"]=="error" for r in rows)/len(rows) if rows else 1
    token_counts=[r["completion_tokens"] for r in successful]
    tokens_per_second=sum(token_counts)/wall_seconds if token_counts and all(t is not None for t in token_counts) and wall_seconds>0 else None
    p95=percentile(latencies,0.95)
    answers=[r["numeric_exact_match"] for r in successful if r["numeric_exact_match"] is not None]
    return {"requests":len(rows),"successful":len(successful),"error_rate":errors,"p50_ttft_ms":percentile(latencies,.5),
            "p95_ttft_ms":p95,"wall_seconds":wall_seconds,"aggregate_tokens_per_second":tokens_per_second,
            "numeric_exact_match":statistics.mean(answers) if answers else None,
            "slo_passed":p95 is not None and p95<=config["maxP95TtftMs"] and errors<=config["maxErrorRate"],
            "sample_note":"Descriptive percentiles; fewer than 100 requests is weak evidence for tail behavior" if len(rows)<100 else "Report uncertainty and repeat independent trials"}


def run_benchmark(config,endpoint=None,model="local",prompts=None):
    c=Experiment.model_validate(config).model_dump()
    prompts=prompts or PROMPTS
    if not prompts: raise ValueError("No prompts")
    workload_hash=hashlib.sha256(json.dumps(prompts,sort_keys=True).encode()).hexdigest()
    mode="live streaming endpoint" if endpoint else "synthetic protocol replay"
    started=time.perf_counter()
    if endpoint:
        for i in range(c["warmupRequests"]):
            warmup=stream_request(endpoint,model,prompts[i%len(prompts)],c)
            if warmup["status"]!="ok": raise RuntimeError("Warmup failed: "+warmup.get("error_type","unknown"))
        started=time.perf_counter()
        with ThreadPoolExecutor(max_workers=c["concurrency"]) as executor:
            rows=list(executor.map(lambda i: stream_request(endpoint,model,prompts[i%len(prompts)],c),range(c["requests"])))
        wall=time.perf_counter()-started
    else:
        rows=[{"prompt_id":prompts[i%len(prompts)]["id"],"status":"ok","ttft_ms":100+15*(i%4)*c["concurrency"],
               "duration_ms":400+10*i,"completion_tokens":c["maxTokens"],"content_chunks":8,"text":"Synthetic fixture; no model was invoked", "numeric_exact_match":None} for i in range(c["requests"])]
        wall=sum(r["duration_ms"] for r in rows)/1000/c["concurrency"]
    signature={"workload_sha256":workload_hash,"model":model,"requests":c["requests"],"concurrency":c["concurrency"],"maxTokens":c["maxTokens"],"mode":mode}
    return {"mode":mode,"summary":summarize(rows,wall,c),"rows":rows,"config":c,"signature":signature,
            "measurement":"Client-observed timing; streamed chunks are not counted as tokens"}


def compare(baseline,candidate):
    if baseline["signature"]!=candidate["signature"]:
        raise ValueError("Baseline and candidate workload/model/mode settings differ; compare equivalent experiments")
    a,b=baseline["summary"]["p95_ttft_ms"],candidate["summary"]["p95_ttft_ms"]
    if a is None or b is None or a<=0: raise ValueError("Both reports need valid positive p95 TTFT")
    change=(b-a)/a
    return {"p95_change_ratio":change,"passed":change<=candidate["config"]["regressionTolerance"] and candidate["summary"]["slo_passed"],
            "tolerance":candidate["config"]["regressionTolerance"]}


def gsm8k_prompts(path,limit=8):
    rows=[json.loads(line) for line in Path(path).read_text().splitlines()[:limit]]
    return [{"id":f"gsm8k-{i}","prompt":r["question"]+"\nEnd with the numeric answer.","answer":r["answer"]} for i,r in enumerate(rows)]


def start_server(model_path,cpus=2,memory_mb=1024):
    path=Path(model_path).expanduser().resolve()
    if not path.is_file() or path.suffix!=".gguf": raise ValueError("Select an existing GGUF model file")
    if not 1<=cpus<=8 or not 512<=memory_mb<=8192: raise ValueError("Invalid VM allocation")
    with socket.socket() as sock:
        sock.bind(("127.0.0.1",0)); port=sock.getsockname()[1]
    runtime=AppleContainer()
    name=runtime.name("inference")
    staging=Path(tempfile.mkdtemp(prefix="lab-model-"))
    shutil.copy2(path,staging/path.name)
    result=runtime.call(["run","-d","--name",name,"--cpus",str(cpus),"--memory",f"{memory_mb}m",
                         "--publish",f"127.0.0.1:{port}:8080","--volume",f"{staging}:/models:ro",
                         "ghcr.io/ggml-org/llama.cpp:server","-m",f"/models/{path.name}","--host","0.0.0.0","--port","8080",
                         "-c","2048","-ngl","0","--parallel","2"],timeout=180)
    if result.returncode:
        runtime.cleanup(name)
        shutil.rmtree(staging)
        raise RuntimeError(result.stderr)
    endpoints=[f"http://127.0.0.1:{port}"]
    inspection=runtime.call(["inspect",name],timeout=10)
    if inspection.returncode==0:
        item=json.loads(inspection.stdout)[0]
        for network in item.get("status",{}).get("networks",[]):
            address=network.get("ipv4Address") or network.get("address")
            if address: endpoints.append("http://"+address.split("/")[0]+":8080")
    session=requests.Session()
    session.trust_env=False
    for _ in range(30):
        for candidate in endpoints:
            try:
                if session.get(candidate+"/health",timeout=.5).status_code==200:
                    return {"name":name,"endpoint":candidate+"/v1","model":path.name,"staging_dir":str(staging)}
            except requests.RequestException: pass
        time.sleep(0.5)
    logs=runtime.call(["logs",name],timeout=5)
    runtime.cleanup(name)
    shutil.rmtree(staging)
    raise RuntimeError("Model server did not become healthy: "+(logs.stdout+logs.stderr)[-2500:])


def stop_server(server):
    AppleContainer().cleanup(server["name"])
    staging=Path(server["staging_dir"]).resolve()
    if staging.parent==Path(tempfile.gettempdir()).resolve() and staging.name.startswith("lab-model-"):
        shutil.rmtree(staging,ignore_errors=True)
