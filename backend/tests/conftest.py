import pytest
from fastapi.testclient import TestClient
from backend import store
from backend.main import app

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(store, 'DATA', tmp_path)
    with TestClient(app) as test_client:
        yield test_client
