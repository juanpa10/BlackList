import os
import json
import pytest
from application import create_app, db, Blacklist  # 👈 importa create_app y modelos

AUTH_HEADERS = {'Authorization': 'Bearer blackSecretToken'}
INVALID_AUTH_HEADERS = {'Authorization': 'Bearer wrongToken'}

@pytest.fixture
def client():
    # ⚙️ Setea valores dummy para evitar conexión real
    os.environ['DB_HOST'] = ''
    os.environ['DB_PORT'] = ''
    os.environ['DB_NAME'] = ''
    os.environ['DB_USER'] = ''
    os.environ['DB_PASSWORD'] = ''

    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.drop_all()

# ✅ Test de health check
def test_health_check(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json == {'healthy': True}

# ✅ Test de éxito al agregar a la lista negra
def test_add_blacklist_success(client):
    test_data = {
        'email': 'test@example.com',
        'app_uuid': '12345678-1234-5678-1234-567812345678',
        'blocked_reason': 'Spam activity'
    }
    response = client.post('/blacklists', data=json.dumps(test_data),
                           headers=AUTH_HEADERS, content_type='application/json')
    assert response.status_code == 201
    assert response.json == {'message': 'Email agregado a la lista negra correctamente'}

# ✅ Test cuando falta el token
def test_add_blacklist_missing_token(client):
    test_data = {
        'email': 'test@example.com',
        'app_uuid': '12345678-1234-5678-1234-567812345678'
    }
    response = client.post('/blacklists', data=json.dumps(test_data),
                           content_type='application/json')
    assert response.status_code == 401

# ✅ Test de verificación de email en la lista negra
def test_check_blacklist_found(client):
    entry = Blacklist(
        email='blacklisted@example.com',
        app_uuid='12345678-1234-5678-1234-567812345678',
        blocked_reason='Spammer',
        ip_address='127.0.0.1'
    )
    with client.application.app_context():
        db.session.add(entry)
        db.session.commit()

    response = client.get('/blacklists/blacklisted@example.com', headers=AUTH_HEADERS)
    assert response.status_code == 200
    assert response.json == {'blacklisted': True, 'blocked_reason': 'Spammer'}