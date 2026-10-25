import csv
import hashlib
import io
import json
import threading
import time
from datetime import date, datetime, timezone
from pathlib import Path
from uuid import uuid4
import httpx
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from . import ai, demo, store, predictive, predictive_demo, tabpfn_adapter
from .engine import detect
from .ingest import FIELDS, parse_file, validate
from .models import Correction, Decision, Mapping, ScanRequest

app = FastAPI(title='QuietOps local API', version='0.1.0')
app.add_middleware(CORSMiddleware, allow_origins=['http://127.0.0.1:3002', 'http://localhost:3002'], allow_methods=['GET','POST'], allow_headers=['Content-Type'])
MUTATION = threading.RLock()

def required(bucket, key):
    result = store.get(bucket, key)
    if not result:
        raise HTTPException(404, 'Record not found.')
    return result

def collect():
    tables = {kind: [] for kind in FIELDS}
    for dataset in store.all_records('datasets'):
        if dataset['confirmed']:
            tables[dataset['kind']].extend(required('validated', dataset['id'])['rows'])
    return tables

def invalidate_predictions(reason):
    report = store.get('meta', 'prediction-run')
    if report:
        report.update({'state': 'stale', 'message': reason})
        store.put('meta', report)
    for action in store.all_records('actions'):
        if action.get('scope') == 'prediction' and action['status'] != 'stale':
            action['status'] = 'stale'
            store.put('actions', action)

def current_prediction(key):
    prediction = required('predictions', key)
    report = store.get('meta', 'prediction-run')
    scan = store.get('meta', 'scan')
    if not report or report['state'] != 'completed' or not scan or prediction['input_fingerprint'] != predictive.input_fingerprint(collect(), scan['as_of']):
        raise HTTPException(409, 'Prediction evidence is stale. Run Looking Ahead again.')
    return prediction

def run_scan(as_of):
    started = time.perf_counter()
    tables = collect()
    if not any(tables.values()):
        raise HTTPException(400, 'Confirm at least one imported dataset before scanning.')
    previous = {i['id']: i for i in store.all_records('issues')}
    issues, inventory = detect(tables, as_of)
    for issue in issues:
        old = previous.get(issue['id'])
        # Only preserve generated text when ALL supplied evidence and facts are unchanged.
        fingerprint = hashlib.sha256(json.dumps({k: issue[k] for k in ('evidence', 'facts', 'assumptions', 'calculation')}, sort_keys=True).encode()).hexdigest()
        issue['fingerprint'] = fingerprint
        if old and old.get('fingerprint') == fingerprint:
            issue['ai'] = old.get('ai')
    store.replace('issues', issues)
    store.replace('inventory', [{**row, 'id': row['sku']} for row in inventory])
    report = store.get('meta', 'prediction-run')
    if report and report.get('input_fingerprint') != predictive.input_fingerprint(tables, as_of):
        invalidate_predictions('Source data or scan date changed. Run predictions again.')
    active = {(i['id'], i['fingerprint']) for i in issues}
    for action in store.all_records('actions'):
        if action.get('scope') == 'prediction':
            continue
        if (action['issue_id'], action.get('fingerprint')) not in active:
            action['status'] = 'stale'
            store.put('actions', action)
    meta = {'id': 'scan', 'as_of': as_of.isoformat(), 'at': datetime.now(timezone.utc).isoformat(), 'latency_ms': round((time.perf_counter()-started)*1000),
            'rows_checked': sum(len(v) for v in tables.values()), 'issues_found': len(issues)}
    store.put('meta', meta)
    store.audit('Scan completed', f"{meta['rows_checked']} valid rows checked; {len(issues)} review candidates; {meta['latency_ms']} ms.")
    return meta

@app.get('/api/health')
def health():
    return {'status': 'ok', 'service': 'QuietOps', 'local': True}

@app.get('/api/model')
async def model():
    return await ai.status()

@app.get('/api/state')
def state():
    with MUTATION:
        datasets = store.all_records('datasets')
        quality = [q for item in store.all_records('quality') for q in item['items']]
        return {'datasets': datasets, 'issues': store.all_records('issues'), 'actions': store.all_records('actions'),
                'inventory': store.all_records('inventory'), 'quality': quality, 'corrections': store.all_records('corrections'),
                'audit': list(reversed(store.all_records('audit'))), 'scan': store.get('meta', 'scan'), 'fields': FIELDS,
                'predictions': store.all_records('predictions'), 'prediction_run': store.get('meta', 'prediction-run'),
                'predictive_model': tabpfn_adapter.status(),
                'synthetic': bool(datasets) and all(d['synthetic'] for d in datasets), 'shop': 'The Corner Store'}

@app.post('/api/import')
async def upload(file: UploadFile = File(...)):
    content = await file.read(15*1024*1024+1)
    try:
        with MUTATION:
            return parse_file(content, file.filename or 'upload.csv')
    except Exception as error:
        if isinstance(error, HTTPException):
            raise
        raise HTTPException(422, str(error)[:400]) from error

@app.post('/api/datasets/{key}/mapping')
def confirm_mapping(key: str, mapping: Mapping):
    with MUTATION:
        dataset = required('datasets', key)
        if dataset['confirmed']:
            raise HTTPException(409, 'This mapping is already confirmed. Import a new file to change it.')
        # Prevent accidental mixing of inventory snapshots and duplicate order-line snapshots.
        if mapping.kind in ('inventory', 'orders') and any(d['confirmed'] and d['kind'] == mapping.kind for d in store.all_records('datasets')):
            raise HTTPException(409, 'A snapshot of this type is already active. Use a separate data directory for a new shop or snapshot.')
        try:
            rows, quality = validate(dataset, required('raw', key)['rows'], mapping)
        except ValueError as error:
            raise HTTPException(422, str(error)) from error
        store.put('validated', {'id': key, 'rows': rows})
        store.put('quality', {'id': key, 'items': quality})
        dataset.update({'confirmed': True, 'mapping': mapping.model_dump(), 'kind': mapping.kind, 'valid_rows': len(rows), 'quality_count': len(quality)})
        store.put('datasets', dataset)
        invalidate_predictions('A mapping was confirmed. Run a check and predictions again.')
        store.audit('Mapping confirmed', f"{dataset['name']}: {len(rows)} valid rows, {len(quality)} validation findings. Currency {mapping.currency}; dates {mapping.date_format}.")
        return dataset

@app.post('/api/demo')
def load_demo():
    with MUTATION:
        existing = store.all_records('datasets')
        if existing:
            raise HTTPException(409, 'This workspace already contains data. Demo loading is available only in an empty workspace; originals and decisions are preserved.')
        for name, content in demo.generate()[0].items():
            dataset = parse_file(content, name, synthetic=True)
            confirm_mapping(dataset['id'], Mapping(**dataset['suggestion']))
        store.audit('Fictional demo loaded', '60 SKUs, 12 suppliers and 90 days of synthetic sales. Demonstration scan date: 2026-10-24.')
        return run_scan(demo.AS_OF)

@app.get('/api/demo/{filename}')
def sample_file(filename: str):
    if filename == 'inventory.xlsx':
        return Response(demo.workbook_sample(), media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', headers={'Content-Disposition': 'attachment; filename="inventory.xlsx"'})
    content = demo.generate()[0].get(filename)
    if not content:
        raise HTTPException(404, 'Sample not found.')
    return Response(content, media_type='text/csv', headers={'Content-Disposition': f'attachment; filename="{filename}"'})

@app.post('/api/scan')
def scan(request: ScanRequest):
    try:
        as_of = date.fromisoformat(request.as_of) if request.as_of else date.today()
        with MUTATION:
            return run_scan(as_of)
    except ValueError as error:
        raise HTTPException(422, str(error)) from error

@app.post('/api/predictions/demo')
def load_prediction_demo():
    with MUTATION:
        datasets = store.all_records('datasets')
        if not datasets or not all(d['synthetic'] for d in datasets):
            raise HTTPException(409, 'Load the original fictional shop first. This companion is only for synthetic workspaces.')
        files = predictive_demo.generate()
        if any(d['name'] in files for d in datasets):
            raise HTTPException(409, 'Predictive companion files already loaded.')
        for name, content in files.items():
            dataset = parse_file(content, name, synthetic=True)
            confirm_mapping(dataset['id'], Mapping(**dataset['suggestion']))
        store.audit('Fictional predictive history loaded', 'Seed 35042; dated stock history and supplemental sales. SKU-007 illustrates recurring synthetic demand, selected after model exploration. Original files preserved.')
        return run_scan(demo.AS_OF)

@app.post('/api/predictions/run')
def run_predictions():
    with MUTATION:
        scan_meta = required('meta', 'scan')
        tables = collect()
        fingerprint = predictive.input_fingerprint(tables, scan_meta['as_of'])
        synthetic = all(d['synthetic'] for d in store.all_records('datasets'))
    try:
        predictions, report = predictive.run(tables, date.fromisoformat(scan_meta['as_of']), synthetic)
    except Exception as error:
        with MUTATION:
            invalidate_predictions('Inference did not complete. No new probabilities were substituted.')
            store.audit('Prediction withheld', f'{type(error).__name__}: {str(error)[:300]}')
        raise HTTPException(503, 'Prediction unavailable. '+str(error)[:400]) from error
    with MUTATION:
        if fingerprint != predictive.input_fingerprint(collect(), required('meta', 'scan')['as_of']):
            raise HTTPException(409, 'Source data changed during inference. Run predictions again.')
        old = {p['id']: p for p in store.all_records('predictions')}
        for prediction in predictions:
            previous = old.get(prediction['id'])
            if previous and previous['fingerprint'] == prediction['fingerprint']:
                prediction['ai'] = previous.get('ai')
        active = {(p['id'], p['fingerprint']) for p in predictions}
        for action in store.all_records('actions'):
            if action.get('scope') == 'prediction' and (action['issue_id'], action['fingerprint']) not in active:
                action['status'] = 'stale'
                store.put('actions', action)
        store.replace('predictions', predictions)
        store.put('meta', report)
        store.audit('TabPFN prediction completed', f"{report['model']['model']}; {report['split']['train_rows']} training rows; {len(predictions)} current estimates; separate from deterministic findings.")
        return report

@app.post('/api/predictions/{key}/explain')
async def explain_prediction(key: str):
    with MUTATION:
        prediction = current_prediction(key)
    try:
        result = await ai.explain(prediction)
    except (httpx.HTTPError, ValueError, KeyError) as error:
        store.audit('Predictive explanation withheld', f'{key}: {str(error)[:180]}')
        raise HTTPException(503, 'Grounded local explanation unavailable. '+str(error)[:250]) from error
    with MUTATION:
        latest = current_prediction(key)
        if latest['fingerprint'] != prediction['fingerprint']:
            raise HTTPException(409, 'Prediction changed during explanation.')
        latest['ai'] = result
        store.put('predictions', latest)
        store.audit('Predictive local AI explanation', f'{ai.MODEL}: {key}; source and numeric guards passed.')
        return latest

@app.post('/api/predictions/{key}/proposal')
def propose_prediction(key: str):
    with MUTATION:
        return make_proposal(current_prediction(key), 'prediction')

@app.post('/api/issues/{key}/explain')
async def explain_issue(key: str):
    issue = required('issues', key)
    try:
        result = await ai.explain(issue)
    except (httpx.HTTPError, ValueError, KeyError) as error:
        store.audit('AI explanation withheld', f'{key}: {str(error)[:180]}')
        raise HTTPException(503, 'Local model unavailable or grounding validation failed. No generated explanation was substituted. '+str(error)[:250]) from error
    with MUTATION:
        latest = required('issues', key)
        if latest['fingerprint'] != issue['fingerprint']:
            raise HTTPException(409, 'Evidence changed during inference. Run explanation again.')
        latest['ai'] = result
        store.put('issues', latest)
        store.audit('Local AI explanation', f"{ai.MODEL}: {key}; source and numeric guards passed; {result['latency_ms']} ms.")
    return latest

@app.post('/api/issues/{key}/proposal')
def propose(key: str):
    with MUTATION:
        issue = required('issues', key)
        return make_proposal(issue)

def make_proposal(issue, scope='issue'):
    key = issue['id']
    if not issue.get('ai'):
        raise HTTPException(409, 'Generate a grounded local explanation before creating an action draft.')
    existing = next((a for a in store.all_records('actions') if a['issue_id'] == key and a.get('fingerprint') == issue['fingerprint'] and a['status'] in ('draft', 'approved')), None)
    if existing:
        return existing
    title = {'stockout': 'Purchase review request', 'late_order': 'Supplier delivery check', 'duplicate_exact': 'Invoice verification request', 'duplicate_fuzzy': 'Invoice verification request', 'predictive_stockout': 'Predictive supplier review request'}[issue['kind']]
    body = f"Subject: {title} — {issue['subject']}\n\nFor review: {issue['supplier']}\n\n{issue['ai']['next_step']}\n\nEvidence: {issue['calculation']}\n\nSources: " + '; '.join(f"{e['file']} / {e['sheet']} / row {e['row']}" for e in issue['evidence']) + '\n\nDraft only. Review original documents, open orders, and assumptions before taking action.'
    action = {'id': uuid4().hex, 'issue_id': key, 'title': title, 'body': body, 'status': 'draft', 'model': issue['ai']['model'],
              'evidence_ids': issue['ai']['evidence_ids'], 'fingerprint': issue['fingerprint'], 'supplier': issue['supplier'], 'scope': scope, 'created_at': datetime.now(timezone.utc).isoformat()}
    store.put('actions', action)
    store.audit('Action drafted', f'{title}: {issue["subject"]}. No message sent or financial record changed.')
    return action


@app.post('/api/actions/{key}/decision')
def decide(key: str, decision: Decision):
    with MUTATION:
        action = required('actions', key)
        if action['status'] != 'draft':
            raise HTTPException(409, 'Only a current draft can receive a decision. Approved exports are immutable.')
        issue = current_prediction(action['issue_id']) if action.get('scope') == 'prediction' else required('issues', action['issue_id'])
        if issue['fingerprint'] != action.get('fingerprint'):
            raise HTTPException(409, 'Evidence changed. Generate a fresh proposal.')
        if decision.body is not None:
            if len(decision.body.strip()) < 10:
                raise HTTPException(422, 'Draft text must contain at least ten characters.')
            action['body'] = decision.body
        action.update({'status': decision.decision, 'decided_at': datetime.now(timezone.utc).isoformat()})
        store.put('actions', action)
        store.put('decisions', {'id': uuid4().hex, 'action_id': key, **decision.model_dump(), 'at': action['decided_at']})
        store.audit('Draft '+decision.decision, f'{action["title"]}: {action["supplier"]}. Approval authorizes export only.')
        return action

@app.get('/api/export/actions')
def export_actions():
    approved = [a for a in store.all_records('actions') if a['status'] == 'approved']
    for action in approved:
        if action.get('scope') == 'prediction':
            current = current_prediction(action['issue_id'])
            if current['fingerprint'] != action['fingerprint']:
                raise HTTPException(409, 'A predictive draft is stale. Run predictions and review again.')
    if not approved:
        raise HTTPException(409, 'Approve at least one current action draft first.')
    body = '# QuietOps — approved action drafts\n\nThese are drafts for manual follow-up. Nothing has been sent or purchased.\n\n' + '\n\n---\n\n'.join(a['body'] for a in approved)
    store.audit('Drafts exported', f'{len(approved)} approved drafts exported for manual review.')
    return Response(body, media_type='text/markdown', headers={'Content-Disposition': 'attachment; filename="quietops-approved-drafts.md"'})

@app.get('/api/datasets/{key}/original')
def original(key: str):
    dataset = required('datasets', key)
    return FileResponse(store.DATA/'originals'/key, filename=dataset['name'], media_type='application/octet-stream')

@app.post('/api/corrections')
def correction(request: Correction):
    dataset = required('datasets', request.dataset_id)
    if request.row > dataset['row_count']+1 or request.field not in (dataset.get('mapping') or {}).get('columns', {}):
        raise HTTPException(422, 'Correction must reference an existing mapped field and source row.')
    row = {'id': uuid4().hex, **request.model_dump(), 'file': dataset['name'], 'status': 'proposed; not applied'}
    store.put('corrections', row)
    store.audit('Correction proposed', f"{dataset['name']}, row {request.row}, {request.field}; original unchanged.")
    return row

@app.get('/api/export/corrections')
def export_corrections():
    output = io.StringIO()
    fields = ['file', 'dataset_id', 'row', 'field', 'proposed_value', 'reason', 'status']
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction='ignore')
    writer.writeheader()
    for item in store.all_records('corrections'):
        # Spreadsheet formula injection protection in exported user-provided text.
        writer.writerow({k: ("'"+str(v) if str(v).startswith(('=', '+', '-', '@', '\t', '\r')) else v) for k, v in item.items()})
    return Response(output.getvalue(), media_type='text/csv', headers={'Content-Disposition': 'attachment; filename="quietops-proposed-corrections.csv"'})
