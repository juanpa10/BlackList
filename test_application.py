import json
import pytest
from application import app, db, Blacklist

AUTH_HEADERS = {'Authorization': 'Bearer blackSecretToken'}
INVALID_AUTH_HEADERS = {'Authorization': 'Bearer wrongToken'}

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.drop_all()

def test_health_check(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json == {'healthy': True}

def test_add_blacklist_success(client):
    test_data = {
        'email': 'test@example.com',
        'app_uuid': '12345678-1234-5678-1234-567812345678',
        'blocked_reason': 'Spam activity'
    }
    response = client.post(
        '/blacklists',
        data=json.dumps(test_data),
        headers=AUTH_HEADERS,
        content_type='application/json'
    )
    assert response.status_code == 201
    assert response.json == {'message': 'Email agregado a la lista negra correctamente'}

def test_add_blacklist_missing_token(client):
    test_data = {
        'email': 'test@example.com',
        'app_uuid': '12345678-1234-5678-1234-567812345678'
    }
    response = client.post(
        '/blacklists',
        data=json.dumps(test_data),
        content_type='application/json'
    )
    assert response.status_code == 401
    assert 'Token ausente o inválido' in response.json['message']

def test_add_blacklist_invalid_token(client):
    test_data = {
        'email': 'test@example.com',
        'app_uuid': '12345678-1234-5678-1234-567812345678'
    }
    response = client.post(
        '/blacklists',
        data=json.dumps(test_data),
        headers=INVALID_AUTH_HEADERS,
        content_type='application/json'
    )
    assert response.status_code == 401
    assert 'Token ausente o inválido' in response.json['message']

def test_add_blacklist_missing_fields(client):
    response = client.post(
        '/blacklists',
        data=json.dumps({'email': 'test@example.com'}),
        headers=AUTH_HEADERS,
        content_type='application/json'
    )
    assert response.status_code == 400
    assert 'Se requieren los campos email y app_uuid' in response.json['message']

    response = client.post(
        '/blacklists',
        data=json.dumps({'app_uuid': '12345678-1234-5678-1234-567812345678'}),
        headers=AUTH_HEADERS,
        content_type='application/json'
    )
    assert response.status_code == 400
    assert 'Se requieren los campos email y app_uuid' in response.json['message']

def test_add_blacklist_invalid_uuid(client):
    test_data = {
        'email': 'test@example.com',
        'app_uuid': 'not-a-valid-uuid'
    }
    response = client.post(
        '/blacklists',
        data=json.dumps(test_data),
        headers=AUTH_HEADERS,
        content_type='application/json'
    )
    assert response.status_code == 400
    assert 'Formato inválido para app_uuid' in response.json['message']

def test_check_blacklist_found(client):
    with app.app_context():
        entry = Blacklist(
            email='blacklisted@example.com',
            app_uuid='12345678-1234-5678-1234-567812345678',
            blocked_reason='Spam activity',
            ip_address='127.0.0.1'
        )
        db.session.add(entry)
        db.session.commit()

    response = client.get(
        '/blacklists/blacklisted@example.com',
        headers=AUTH_HEADERS
    )
    assert response.status_code == 200
    assert response.json == {
        'blacklisted': True,
        'blocked_reason': 'Spam activity'
    }

def test_check_blacklist_not_found(client):
    response = client.get(
        '/blacklists/clean@example.com',
        headers=AUTH_HEADERS
    )
    assert response.status_code == 200
    assert response.json == {
        'blacklisted': False,
        'blocked_reason': None
    }

def test_check_blacklist_missing_token(client):
    response = client.get('/blacklists/test@example.com')
    assert response.status_code == 401
    assert 'Token ausente o inválido' in response.json['message']

def test_check_blacklist_invalid_token(client):
    response = client.get(
        '/blacklists/test@example.com',
        headers=INVALID_AUTH_HEADERS
    )
    assert response.status_code == 401
    assert 'Token ausente o inválido' in response.json['message']
