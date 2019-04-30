from flask import Flask
import json
from dateutil import parser

from tests.utils import Utils
from app.api import require_admin


# Authentication Tests

def test_authentication(app, client):
    # create default roles and accounts
    Utils(app, client)
    # get a token
    resp = client.post('/api/auth', json={'username': 'test', 'password': 'password_for_test'})
    assert resp.status_code == 200
    assert 'accessToken' in json.loads(resp.data.decode())
    assert 'refreshToken' in json.loads(resp.data.decode())


def test_authentication_invalid_password(app, client):
    Utils(app, client)
    resp = client.post('/api/auth', json={'username': 'test', 'password': 'invalid'})
    assert resp.status_code == 401
    assert json.loads(resp.data.decode('utf8')).get('message') == 'Invalid credentials'


def test_authentication_invalid_credentials(app, client):
    Utils(app, client)
    resp = client.post('/api/auth', json={'username': 'invalid', 'password': 'invalid'})
    assert resp.status_code == 401
    assert json.loads(resp.data.decode('utf8')).get('message') == 'Invalid credentials'


def test_authentication_without_data(app, client):
    resp = client.post('/api/auth')
    assert resp.status_code == 400


def test_authentication_invalid_data(app, client):
    resp = client.post('/api/auth', json={'invalid': 'test', 'password': 'password_for_test'})
    assert resp.status_code == 400

# End of Authentication Tests


# getUserInfo Tests

def test_get_user_info(app, client):
    utils = Utils(app, client)
    resp = client.get('/api/auth', headers={'Authorization': f'Bearer {utils.generate_access_token()}'})
    assert resp.status_code == 200
    assert 'username' in json.loads(resp.data.decode()).get('data')
    assert parser.parse(json.loads(resp.data.decode()).get('data').get('created'))


def test_get_user_info_without_token(app, client):
    with app.app_context():
        resp = client.get('/api/auth')
        assert resp.status_code == 401
        assert json.loads(resp.data.decode('utf8')).get('message') == 'Missing access token'


def test_get_user_info_invalid_token(app, client):
    with app.app_context():
        resp = client.get('/api/auth', headers={'Authorization': 'Bearer invalid'})
        assert resp.status_code == 401
        assert json.loads(resp.data.decode('utf8')).get('message') == 'Invalid access token'

# End of getUserInfo Tests


# decorator @require_admin before @require_token
def test_require_admin_without_require_token():
    app = Flask(__name__)

    @app.route('/')
    @require_admin
    def index():
        pass

    client = app.test_client()
    resp = client.get('/')
    assert resp.status_code == 500
