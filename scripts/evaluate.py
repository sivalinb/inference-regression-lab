from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from labcore.ai import retrieve,ask
from labcore.config import load_config
docs=json.loads((ROOT/'data/knowledge.json').read_text())
queries=[('What makes metric labels create too many time series?','metrics'),('Can queued telemetry survive a crash using durable storage?','recovery'),('How should streamed chunks be used for token throughput?','inference'),('Why do host and guest memory measurements differ?','resources'),('How do VM mounts affect isolated job security?','isolation')]
cases=[{'question':q,'expected':expected,'retrieved':[d['id'] for d in retrieve(q,docs)]} for q,expected in queries]
hits=sum(c['expected'] in c['retrieved'] for c in cases)
abstained=ask('sourdough rye recipe kneading',docs)['abstained']
config,_=load_config(ROOT)
checks=[]
from engine import run_benchmark,compare
import copy
a=run_benchmark(config)
b=copy.deepcopy(a)
b['summary']['p95_ttft_ms']*=1.5
checks=[{'case':'same baseline','passed':compare(a,a)['passed']},{'case':'50 percent regression','passed':not compare(a,b)['passed']}]
report={'retrieval_hit_at_3':hits/len(cases),'abstention_passed':abstained,'retrieval_cases':cases,'domain_checks':checks,'mode':'offline evaluation; no live runtime or model claims'}
report['passed']=hits/len(cases)>=.8 and abstained and all(x['passed'] for x in checks)
(ROOT/'artifacts').mkdir(exist_ok=True)
(ROOT/'artifacts/evaluation.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
if not report['passed']: raise SystemExit(1)
