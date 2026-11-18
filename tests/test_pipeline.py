"""Checks the trained artifacts and the FastAPI endpoints. Run after train.py."""
import hashlib
import json
import os
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app import app

CONFIG = json.loads(Path('config.json').read_text())
DATASET = Path('dataset/train.csv')
METRICS = Path('artifacts/metrics.json')


@pytest.fixture(scope='module')
def metrics():
    assert METRICS.exists(), 'Run train.py before the tests'
    return json.loads(METRICS.read_text())


@pytest.fixture(scope='module')
def client():
    return TestClient(app)


def test_metrics_have_required_fields(metrics):
    for field in ('student_id', 'accuracy', 'training_rows', 'model_version', 'git_sha'):
        assert field in metrics
    assert metrics['student_id'] == CONFIG['student_id']


def test_training_rows_match_dataset(metrics):
    assert metrics['training_rows'] == len(pd.read_csv(DATASET))


def test_model_version_matches_dataset(metrics):
    assert metrics['model_version'] == hashlib.sha256(DATASET.read_bytes()).hexdigest()[:12]


def test_accuracy_is_reasonable(metrics):
    assert 0.5 <= metrics['accuracy'] <= 1.0


def test_git_sha_matches_build_commit(metrics):
    commit = os.environ.get('GIT_COMMIT')
    if not commit:
        pytest.skip('GIT_COMMIT is only set in Jenkins')
    assert metrics['git_sha'] == commit


def test_health_and_metrics_endpoints(client, metrics):
    assert client.get('/health').json() == {'status': 'ok'}
    assert client.get('/metrics').json() == metrics


def test_predict_returns_binary_predictions(client):
    features = CONFIG['features']
    records = [dict.fromkeys(features, 0.5), {features[0]: 1.2}]  # second record has missing values
    response = client.post('/predict', json={'records': records})
    assert response.status_code == 200
    body = response.json()
    assert len(body['predictions']) == 2
    assert set(body['predictions']) <= {0, 1}
    assert all(0 <= p <= 1 for p in body['probabilities'])


def test_predict_rejects_empty_request(client):
    assert client.post('/predict', json={'records': []}).status_code == 422
