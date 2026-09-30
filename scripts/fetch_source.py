from pathlib import Path
import argparse,json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from labcore.sources import catalogue,fetch_source
parser=argparse.ArgumentParser()
parser.add_argument('source_id',choices=[x['id'] for x in catalogue(ROOT)])
args=parser.parse_args()
print(json.dumps(fetch_source(ROOT,args.source_id),indent=2))
