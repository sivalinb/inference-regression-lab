import copy
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import json
from pathlib import Path
import threading
import time
import pytest
from labcore.config import load_config
from engine import stream_request,summarize,compare,run_benchmark,numeric_answer,PROMPTS

@pytest.fixture
def config():
    c=load_config(Path(__file__).resolve().parents[1])[0]
    c['requests']=3
    return c

@pytest.fixture
def endpoint():
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def do_POST(self):
            body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            self.send_response(200)
            self.send_header('Content-Type','text/event-stream')
            self.end_headers()
            chunks=[{'choices':[{'delta':{'role':'assistant'}}]},
                    {'choices':[{'delta':{'content':'4'}}]},
                    {'choices':[{'delta':{'content':'2'}}]},
                    {'choices':[],'usage':{'completion_tokens':2}}]
            try:
                for c in chunks:
                    time.sleep(.01)
                    self.wfile.write(('data: '+json.dumps(c)+'\n\n').encode()); self.wfile.flush()
                self.wfile.write(b'data: [DONE]\n\n'); self.wfile.flush()
            except (BrokenPipeError,ConnectionResetError): pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    yield f'http://127.0.0.1:{server.server_port}/v1'
    server.shutdown();server.server_close();thread.join(timeout=2)

def test_real_sse_transport_measures_content_not_role(endpoint,config):
    r=stream_request(endpoint,'test-fixture',PROMPTS[0],config)
    assert r['status']=='ok'
    assert r['text']=='42'
    assert r['completion_tokens']==2
    assert r['content_chunks']==2
    assert r['ttft_ms']>=15
    assert r['numeric_exact_match'] is True

def test_cancel_stream(endpoint,config):
    r=stream_request(endpoint,'test-fixture',PROMPTS[0],config,cancel_after=1)
    assert r['status']=='cancelled'
    assert r['text']=='4'

def test_live_batch_request_count(endpoint,config):
    r=run_benchmark(config,endpoint,'test-fixture')
    assert r['summary']['successful']==3
    assert r['summary']['aggregate_tokens_per_second']>0

def test_no_usage_never_guesses_tokens(config):
    r=summarize([{'status':'ok','ttft_ms':3,'completion_tokens':None,'numeric_exact_match':None}],1,config)
    assert r['aggregate_tokens_per_second'] is None

def test_regression_gate(config):
    a=run_benchmark(config)
    b=copy.deepcopy(a);b['summary']['p95_ttft_ms']*=1.5
    assert compare(a,a)['passed']
    assert not compare(a,b)['passed']

def test_incompatible_baseline_rejected(config):
    a=run_benchmark(config)
    b=run_benchmark(dict(config,concurrency=3))
    with pytest.raises(ValueError,match='differ'): compare(a,b)

def test_numeric_answer_gsm8k_format():
    assert numeric_answer('Reasoning 20 plus 22. #### 42')=='42'
    assert numeric_answer('The answer is 1,200')=='1200'

def test_remote_plaintext_endpoint_rejected(config):
    with pytest.raises(ValueError,match='HTTPS'): stream_request('http://example.com/v1','x',PROMPTS[0],config)

@pytest.mark.parametrize('lines',[[b'data: not-json'],[b'data: {"choices":[{"delta":{"content":"partial"}}]}']])
def test_malformed_or_incomplete_stream_is_error(config,monkeypatch,lines):
    class Response:
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def raise_for_status(self): pass
        def iter_lines(self,**kwargs): return iter(lines)
    class Session:
        def post(self,*args,**kwargs): return Response()
    monkeypatch.setattr('engine.requests.Session',Session)
    r=stream_request('http://127.0.0.1:1234/v1','fixture',PROMPTS[0],config)
    assert r['status']=='error'
