"""Reproducible fixture evaluation; never claims field performance or measured time savings."""
import argparse
import asyncio
import json
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from fastapi.testclient import TestClient
from backend import ai, demo, store
from backend.main import app

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--real-ai', action='store_true')
    parser.add_argument('--output', default='docs/evaluation-results.json')
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='quietops-eval-') as directory:
        store.DATA = Path(directory)
        with TestClient(app) as client:
            started = time.perf_counter()
            response = client.post('/api/demo')
            response.raise_for_status()
            state = client.get('/api/state').json()
            ground_truth = demo.generate()[1]
            results = {}
            for kind, labels in ground_truth.items():
                expected = set(labels)
                observed = {i['subject'] for i in state['issues'] if i['kind']==kind}
                true_positive = len(expected & observed)
                results[kind] = {'tp':true_positive,'fp':len(observed-expected),'fn':len(expected-observed),
                                 'precision':true_positive/len(observed) if observed else 0,
                                 'recall':true_positive/len(expected) if expected else 0}
            report = {'at':datetime.now(timezone.utc).isoformat(),'dataset':'Explicitly fictional seed 42; 60 SKUs / 12 suppliers / 90 days',
                      'scope':'In-distribution synthetic fixture only, not real shop accuracy; detector thresholds are not independently tuned.',
                      'rows':state['scan']['rows_checked'],'issues':len(state['issues']), 'scan_latency_ms':state['scan']['latency_ms'],
                      'demo_import_and_scan_ms':round((time.perf_counter()-started)*1000),'detectors':results,
                      'measured_human_time_saved':None,'real_ai':[]}
            if args.real_ai:
                for kind in ground_truth:
                    issue = next(i for i in state['issues'] if i['kind']==kind)
                    started = time.perf_counter()
                    response = client.post(f"/api/issues/{issue['id']}/explain")
                    entry = {'kind':kind,'http_status':response.status_code,'wall_ms':round((time.perf_counter()-started)*1000)}
                    if response.status_code==200:
                        generated = response.json()['ai']
                        entry.update(generated)
                        entry['guards_passed']=True
                    else:
                        entry.update({'guards_passed':False,'error':response.text})
                    report['real_ai'].append(entry)
            output = Path(args.output)
            output.parent.mkdir(parents=True,exist_ok=True)
            output.write_text(json.dumps(report,indent=2),encoding='utf-8')
            print(json.dumps(report,indent=2))
            if any(r['fp'] or r['fn'] for r in results.values()):
                raise SystemExit('Detector fixture mismatch.')
            if args.real_ai and any(not entry['guards_passed'] for entry in report['real_ai']):
                raise SystemExit('A real AI evaluation failed; inspect the recorded result.')

if __name__=='__main__':
    main()
