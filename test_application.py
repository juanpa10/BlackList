import json
import pytest
from unittest.mock import patch, MagicMock
from application import app, Blacklist, db

@pytest.fixture
def client():
    """Create a test client for the app."""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.drop_all()

def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json == {'healthy': True}

class TestBlacklistEndpoints:
    AUTH_HEADERS = {'Authorization': 'Bearer blackSecretToken'}
    INVALID_AUTH_HEADERS = {'Authorization': 'Bearer wrongToken'}
    
    def test_add_blacklist_success(self, client):
        """Test successfully adding an email to blacklist."""
        test_data = {
            'email': 'test@example.com',
            'app_uuid': '12345678-1234-5678-1234-567812345678',
            'blocked_reason': 'Spam activity'
        }
        
        with patch('application.Blacklist') as MockBlacklist:
            mock_instance = MagicMock()
            MockBlacklist.return_value = mock_instance
            
            with patch('application.db.session.add'), patch('application.db.session.commit'):
                response = client.post(
                    '/blacklists',
                    data=json.dumps(test_data),
                    headers=self.AUTH_HEADERS,
                    content_type='application/json'
                )
                
                assert response.status_code == 201
                assert response.json == {'message': 'Email agregado a la lista negra correctamente'}

    def test_add_blacklist_missing_token(self, client):
        """Test adding to blacklist with missing auth token."""
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

    def test_add_blacklist_invalid_token(self, client):
        """Test adding to blacklist with invalid auth token."""
        test_data = {
            'email': 'test@example.com',
            'app_uuid': '12345678-1234-5678-1234-567812345678'
        }
        
        response = client.post(
            '/blacklists',
            data=json.dumps(test_data),
            headers=self.INVALID_AUTH_HEADERS,
            content_type='application/json'
        )
        
        assert response.status_code == 401
        assert 'Token ausente o inválido' in response.json['message']

    def test_add_blacklist_missing_fields(self, client):
        """Test adding to blacklist with missing required fields."""
        # Missing app_uuid
        test_data = {'email': 'test@example.com'}
        
        response = client.post(
            '/blacklists',
            data=json.dumps(test_data),
            headers=self.AUTH_HEADERS,
            content_type='application/json'
        )
        
        assert response.status_code == 400
        assert 'Se requieren los campos email y app_uuid' in response.json['message']
        
        # Missing email
        test_data = {'app_uuid': '12345678-1234-5678-1234-567812345678'}
        
        response = client.post(
            '/blacklists',
            data=json.dumps(test_data),
            headers=self.AUTH_HEADERS,
            content_type='application/json'
        )
        
        assert response.status_code == 400
        assert 'Se requieren los campos email y app_uuid' in response.json['message']

    def test_add_blacklist_invalid_uuid(self, client):
        """Test adding to blacklist with invalid UUID format."""
        test_data = {
            'email': 'test@example.com',
            'app_uuid': 'not-a-valid-uuid'
        }
        
        response = client.post(
            '/blacklists',
            data=json.dumps(test_data),
            headers=self.AUTH_HEADERS,
            content_type='application/json'
        )
        
        assert response.status_code == 400
        assert 'Formato inválido para app_uuid' in response.json['message']

    def test_check_blacklist_found(self, client):
        """Test checking if an email is blacklisted (found)."""
        test_email = 'blacklisted@example.com'
        
        with patch('application.Blacklist.query') as mock_query:
            mock_query.filter_by.return_value.first.return_value = MagicMock(
                email=test_email,
                blocked_reason='Spam activity'
            )
            
            response = client.get(
                f'/blacklists/{test_email}',
                headers=self.AUTH_HEADERS
            )
            
            assert response.status_code == 200
            assert response.json == {
                'blacklisted': True,
                'blocked_reason': 'Spam activity'
            }
            
            # Verify the mock was called with the correct email
            mock_query.filter_by.assert_called_once_with(email=test_email)

    def test_check_blacklist_not_found(self, client):
        """Test checking if an email is blacklisted (not found)."""
        test_email = 'clean@example.com'
        
        with patch('application.Blacklist.query') as mock_query:
            mock_query.filter_by.return_value.first.return_value = None
            
            response = client.get(
                f'/blacklists/{test_email}',
                headers=self.AUTH_HEADERS
            )
            
            assert response.status_code == 200
            assert response.json == {
                'blacklisted': False,
                'blocked_reason': None
            }
            
            # Verify the mock was called with the correct email
            mock_query.filter_by.assert_called_once_with(email=test_email)

    def test_check_blacklist_missing_token(self, client):
        """Test checking blacklist without auth token."""
        response = client.get('/blacklists/test@example.com')
        
        assert response.status_code == 401
        assert 'Token ausente o inválido' in response.json['message']

    def test_check_blacklist_invalid_token(self, client):
        """Test checking blacklist with invalid auth token."""
        response = client.get(
            '/blacklists/test@example.com',
            headers=self.INVALID_AUTH_HEADERS
        )
        
        assert response.status_code == 401
        assert 'Token ausente o inválido' in response.json['message']