from app.api import require_admin
import json
from dateutil import parser
from flask import Flask
from .utils import get_user_token, create_dummy_user


def test_auth(app, client):
    with app.app_context():
        create_dummy_user(app, client)
        resp = client.post('/api/auth', json={'username': 'test', 'password': 'test'})
        assert resp.status_code == 200
        assert 'token' in json.loads(resp.data.decode())


def test_auth_invalid_credentials(app, client):
    with app.app_context():
        resp = client.post('/api/auth', json={'username': 'test', 'password': 'test'})
        assert resp.status_code == 401
        assert json.loads(resp.data.decode('utf8')).get('message') == 'Wrong credentials'


def test_auth_without_data(app, client):
    with app.app_context():
        resp = client.post('/api/auth')
        assert resp.status_code == 400


def test_get_user_data(app, client):
    with app.app_context():
        token = get_user_token(app, client)
        resp = client.get('/api/auth', headers={'Access-Token': token})
        assert resp.status_code == 200
        assert 'username' in json.loads(resp.data.decode()).get('data')
        assert parser.parse(json.loads(resp.data.decode()).get('data').get('created'))


def test_get_user_data_without_token(app, client):
    with app.app_context():
        resp = client.get('/api/auth')
        assert resp.status_code == 401
        assert json.loads(resp.data.decode('utf8')).get('message') == 'Missing Access-Token'


def test_get_user_data_invalid_token(app, client):
    with app.app_context():
        resp = client.get('/api/auth', headers={'Access-Token': 'I am a test token!'})
        assert resp.status_code == 401
        assert json.loads(resp.data.decode('utf8')).get('message') == 'Invalid Access-Token'


def test_require_admin_without_require_token():
    app = Flask(__name__)

    @app.route('/')
    @require_admin
    def index(): pass
    client = app.test_client()
    resp = client.get('/')
    assert resp.status_code == 500
