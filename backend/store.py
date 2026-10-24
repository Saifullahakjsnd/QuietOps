import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(os.environ.get('QUIETOPS_DATA', ROOT / 'data'))

@contextmanager
def connection():
    DATA.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DATA / 'quietops.sqlite3', timeout=30)
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('CREATE TABLE IF NOT EXISTS records (bucket TEXT, id TEXT, value TEXT, PRIMARY KEY(bucket,id))')
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def put(bucket, item):
    with connection() as db:
        db.execute('INSERT OR REPLACE INTO records VALUES (?,?,?)', (bucket, item['id'], json.dumps(item, allow_nan=False)))
    return item

def get(bucket, key):
    with connection() as db:
        row = db.execute('SELECT value FROM records WHERE bucket=? AND id=?', (bucket, key)).fetchone()
    return json.loads(row[0]) if row else None

def all_records(bucket):
    with connection() as db:
        rows = db.execute('SELECT value FROM records WHERE bucket=? ORDER BY rowid', (bucket,)).fetchall()
    return [json.loads(row[0]) for row in rows]

def replace(bucket, items):
    with connection() as db:
        db.execute('DELETE FROM records WHERE bucket=?', (bucket,))
        db.executemany('INSERT INTO records VALUES (?,?,?)', [(bucket, item['id'], json.dumps(item, allow_nan=False)) for item in items])

def audit(action, detail):
    return put('audit', {'id': uuid4().hex, 'at': datetime.now(timezone.utc).isoformat(), 'action': action, 'detail': detail})
