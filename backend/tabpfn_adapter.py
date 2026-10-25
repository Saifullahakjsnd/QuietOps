"""Optional local TabPFN-3.5 only. Never substitutes another model or fake probabilities."""
import hashlib
import importlib.metadata
import importlib.util
import os
import shutil
import time
import threading
from uuid import uuid4
from . import store

MODEL = 'TabPFN-3.5'
CHECKPOINT = 'tabpfn-v3.5-20260909.safetensors'
REPOSITORY = 'Prior-Labs/tabpfn_3_5'
REVISION = 'b0662010dd17679509f42326e2f9ba37a6f58818'
CHECKPOINT_SHA256 = 'ece4d67eadfea42eb0e610df5189bea60cb7f31073d81e9c7a019b76eacf0be3'
INFERENCE_LOCK = threading.Lock()
LICENSE_URL = 'https://huggingface.co/Prior-Labs/tabpfn_3_5/blob/main/LICENSE'

def status():
    accepted = os.getenv('QUIETOPS_TABPFN_LICENSE_ACCEPTED', '').lower() == 'yes' or bool(store.get('meta', 'tabpfn-license'))
    installed = importlib.util.find_spec('tabpfn') is not None
    disabled = os.getenv('QUIETOPS_TABPFN_ENABLED', '1').lower() in ('0', 'false', 'no')
    state = 'disabled' if disabled else 'license_required' if not accepted else 'not_installed' if not installed else 'ready'
    failure = store.get('meta', 'tabpfn-error') if state == 'ready' else None
    message = {'disabled': 'Predictive inference is disabled by configuration.',
               'license_required': 'Accept the non-commercial model license before enabling inference.',
               'not_installed': 'Install backend/requirements-tabpfn.txt in the backend environment.',
               'ready': 'Ready to attempt local inference; checkpoint access is verified on first run.'}[state]
    return {'state': 'error' if failure else state, 'available': state == 'ready', 'model': MODEL, 'checkpoint': CHECKPOINT,
            'repository': REPOSITORY, 'package_version': importlib.metadata.version('tabpfn') if installed else None,
            'license_url': LICENSE_URL, 'license_accepted': accepted,
            'device': os.getenv('QUIETOPS_TABPFN_DEVICE', 'cpu'),
            'message': failure['message']+' Retry is available.' if failure else message}

def predict(train, labels, test):
    try:
        with INFERENCE_LOCK:
            result = _predict(train, labels, test)
    except Exception as error:
        if status()['available']:
            store.put('meta', {'id': 'tabpfn-error', 'message': f'Inference failed ({type(error).__name__}); inspect the local backend log and model setup.'})
        raise
    # Remove the last failure only after actual success.
    with store.connection() as db:
        db.execute("DELETE FROM records WHERE bucket='meta' AND id='tabpfn-error'")
    return result

def _predict(train, labels, test):
    current = status()
    if not current['available']:
        raise RuntimeError(current['message'])
    if len(train) > 2000 or len(test) > 2000:
        raise ValueError('This local adapter supports at most 2,000 training and 2,000 prediction rows per run; curate history first.')
    if len(set(labels)) != 2:
        raise ValueError('Historical training data must contain both outcomes.')
    # Public manual-download workflow, after explicit license acceptance. No account token is logged.
    from huggingface_hub import hf_hub_download
    checkpoint_path = hf_hub_download(REPOSITORY, CHECKPOINT, revision=REVISION)
    # tabpfn 9.2 resolves symlinks before detecting the format. HF's blob targets
    # have no suffix, which makes upstream incorrectly try pickle. Materialize
    # a regular .safetensors file; never weaken torch.load's safety settings.
    materialized = store.ROOT / 'data' / 'models' / REVISION / CHECKPOINT
    if not materialized.exists():
        materialized.parent.mkdir(parents=True, exist_ok=True)
        temporary = materialized.with_name(CHECKPOINT+'.'+uuid4().hex+'.download')
        shutil.copyfile(checkpoint_path, temporary)
        temporary.replace(materialized)
    checkpoint_path = str(materialized)
    with open(checkpoint_path, 'rb') as checkpoint_file:
        checkpoint_hash = hashlib.file_digest(checkpoint_file, 'sha256').hexdigest()
    if checkpoint_hash != CHECKPOINT_SHA256:
        raise RuntimeError('Checkpoint checksum does not match the pinned official TabPFN-3.5 release; inference withheld.')
    # Optional import keeps the existing deterministic application usable without PyTorch.
    os.environ.setdefault('TABPFN_NO_BROWSER', '1')
    from tabpfn import TabPFNClassifier
    from tabpfn.constants import ModelVersion
    import numpy as np
    import torch
    torch.set_num_threads(min(8, os.cpu_count() or 1))
    started = time.perf_counter()
    model = TabPFNClassifier.create_default_for_version(
        ModelVersion.V3_5, model_path=checkpoint_path, device=current['device'], n_estimators=2, random_state=42,
        n_jobs=1)
    model.fit(train, labels)
    probabilities = model.predict_proba(test)[:, list(model.classes_).index(1)]
    if not np.isfinite(probabilities).all() or ((probabilities < 0) | (probabilities > 1)).any():
        raise RuntimeError('Model returned invalid probabilities; results withheld.')
    # Record the checkpoint actually loaded, including its byte hash where available.
    metadata = {**current, 'state': 'inference_completed', 'inference_ran': True,
                'revision': REVISION, 'checkpoint_sha256': checkpoint_hash,
                'latency_ms': round((time.perf_counter()-started)*1000),
                'n_estimators': 2, 'seed': 42, 'torch_version': torch.__version__,
                'training_rows': len(train), 'prediction_rows': len(test)}
    return probabilities.tolist(), metadata
