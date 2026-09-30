from pathlib import Path
import argparse,json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from labcore.config import load_config
from labcore.observability import Recorder
config,meta=load_config(ROOT)
parser=argparse.ArgumentParser()
parser.add_argument('--live',action='store_true')
recorder=Recorder(ROOT,ROOT.name)
with recorder.span('cli_run'):
    from engine import run_benchmark
    parser.add_argument('--endpoint')
    parser.add_argument('--model',default='local')
    args=parser.parse_args()
    if args.live and not args.endpoint: parser.error('--live requires --endpoint for a running model server')
    report=run_benchmark(config,args.endpoint,args.model)
report['config_provenance']=meta
recorder.save(report)
(ROOT/'artifacts/cli-latest.json').write_text(json.dumps(report,indent=2,allow_nan=False))
print(json.dumps(report,indent=2,allow_nan=False))
if report.get('passed') is False: raise SystemExit(1)
