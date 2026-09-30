import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import pytest
from labcore.config import load_config
from labcore.runtime import command,AppleContainer
from labcore.ai import retrieve,ask
from labcore.observability import Recorder

ROOT=Path(__file__).resolve().parents[1]

def test_snapshot_matches_source():
    snapshot=json.loads((ROOT/'config/default.json').read_text())
    assert snapshot['source_sha256']==hashlib.sha256((ROOT/'config/default.pkl').read_bytes()).hexdigest()

def test_stale_snapshot_rejected(tmp_path,monkeypatch):
    (tmp_path/'config').mkdir()
    (tmp_path/'config/default.pkl').write_text('x = 1')
    (tmp_path/'config/default.json').write_text(json.dumps({'source_sha256':'wrong','config':{}}))
    monkeypatch.delenv('PKL_BIN',raising=False)
    monkeypatch.setattr('labcore.config.shutil.which',lambda _:None)
    with pytest.raises(ValueError,match='stale'): load_config(tmp_path)

def test_pkl_constraints_reject_invalid_allocation(tmp_path):
    import shutil
    binary=os.environ.get('PKL_BIN') or shutil.which('pkl')
    if not binary: pytest.skip('Native Pkl unavailable; CI installs it')
    source=(ROOT/'config/default.pkl').as_uri()
    path=tmp_path/'invalid.pkl'
    path.write_text('amends "'+source+'"\ncpus = 0\n')
    result=subprocess.run([binary,'eval',str(path)],capture_output=True,text=True,timeout=30)
    assert result.returncode!=0
    assert 'constraint' in result.stderr.lower()

def test_subprocess_deadline():
    result=command([sys.executable,'-c','import time;time.sleep(5)'],timeout=.1)
    assert result.reason=='timeout'
    assert result.duration_s<3

def test_subprocess_output_budget():
    result=command([sys.executable,'-c','while True: print("x"*8192,flush=True)'],timeout=3,max_output=1000)
    assert result.reason=='output_limit'
    assert len(result.stdout.encode())<=1000

def test_cleanup_refuses_foreign_resources():
    with pytest.raises(ValueError): AppleContainer().cleanup('production-database')

def test_unrelated_question_abstains():
    docs=json.loads((ROOT/'data/knowledge.json').read_text())
    assert ask('sourdough rye recipe kneading',docs)['abstained']

def test_retrieval_cites_relevant_evidence():
    docs=json.loads((ROOT/'data/knowledge.json').read_text())
    assert 'metrics' in {d['id'] for d in retrieve('unbounded label cardinality time series',docs)}

def test_recorder_has_no_input_payload(tmp_path):
    r=Recorder(tmp_path,'test-lab')
    with r.span('test',mode='fixture',secret='never-record-this'): pass
    event=(tmp_path/'artifacts/events.jsonl').read_text()
    assert 'never-record-this' not in event
    assert json.loads(event)['status']=='ok'
    assert b'lab_operations_total' in (tmp_path/'artifacts/metrics.prom').read_bytes()

@pytest.mark.parametrize('answer,abstained',[('Counters need bounded labels [metrics].',False),('A claim with [invented].',True),('An uncited claim.',True)])
def test_model_citation_membership_gate(monkeypatch,answer,abstained):
    docs=json.loads((ROOT/'data/knowledge.json').read_text())
    class Response:
        def raise_for_status(self): pass
        def json(self): return {'choices':[{'message':{'content':answer}}]}
    class Session:
        def post(self,*args,**kwargs): return Response()
    monkeypatch.setattr('labcore.ai.requests.Session',Session)
    r=ask('unbounded label cardinality time series',docs,endpoint='http://127.0.0.1:1/v1',model='fixture')
    assert r['abstained'] is abstained

def test_source_allowlist_prevents_arbitrary_fetch(tmp_path,monkeypatch):
    from labcore.sources import fetch_source
    monkeypatch.setattr('labcore.sources.catalogue',lambda _: [{'id':'bad','download_url':'http://169.254.169.254/latest/meta-data'}])
    with pytest.raises(ValueError,match='allowlist'): fetch_source(tmp_path,'bad')
