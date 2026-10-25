"""Reproduce the fictional chronological benchmark with genuine TabPFN inference."""
import argparse
import json
from pathlib import Path
from datetime import date
from backend import store, demo, predictive, predictive_demo
from backend.ingest import parse_file
from backend.main import collect, confirm_mapping, run_scan
from backend.models import Mapping

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-dir', default='data/tabpfn-evaluation')
    parser.add_argument('--output', default='docs/tabpfn-evaluation.json')
    args = parser.parse_args()
    store.DATA = Path(args.data_dir).resolve()
    if store.all_records('datasets'):
        raise SystemExit('Evaluation requires an empty data directory. Use a new --data-dir; originals are never deleted.')
    files = {**demo.generate()[0], **predictive_demo.generate()}
    for name, content in files.items():
        dataset = parse_file(content, name, synthetic=True)
        confirm_mapping(dataset['id'], Mapping(**dataset['suggestion']))
    run_scan(demo.AS_OF)
    tables = collect()
    predictions, report = predictive.run(tables, demo.AS_OF, synthetic=True)
    report['fixture'] = {'original_seed': 42, 'companion_seed': predictive_demo.SEED,
                         'files': {d['name']: d['sha256'] for d in store.all_records('datasets')}}
    store.replace('predictions', predictions)
    store.put('meta', report)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, allow_nan=False), encoding='utf-8')
    output.with_name('tabpfn-live-predictions.json').write_text(json.dumps(predictions, indent=2, allow_nan=False), encoding='utf-8')
    print(json.dumps({'model': report['model'], 'split': report['split'], 'comparison': report['comparison'],
                      'overlooked': [{'sku': p['subject'], 'probability': p['facts']['probability']} for p in predictions if p['overlooked_by_rule']]}, indent=2))

if __name__ == '__main__':
    main()
