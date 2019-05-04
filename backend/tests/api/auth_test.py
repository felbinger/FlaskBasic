from flask import Flask
import json
from dateutil import parser

from tests.utils import Utils
from app.api import require_admin


def test_authentication(app, client):
    Utils(app, client)
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


def test_authentication_with_2fa(app, client):
    utils = Utils(app, client)
    utils.enable_2fa()

    # request should result in an error, because the 2fa token is missing
    resp = client.post('/api/auth', json={'username': 'test', 'password': 'password_for_test'})
    assert resp.status_code == 401
    assert json.loads(resp.data.decode('utf8')).get('message') == 'Missing 2fa token'

    # the 2fa token is in the data of this request, so it should work
    resp = client.post(
        '/api/auth',
        json={'username': 'test', 'password': 'password_for_test', 'token': utils.generate_2fa_token()}
    )
    assert resp.status_code == 200
    assert 'accessToken' in json.loads(resp.data.decode())
    assert 'refreshToken' in json.loads(resp.data.decode())


def test_authentication_with_invalid_2fa_token(app, client):
    utils = Utils(app, client)
    utils.enable_2fa()

    resp = client.post(
        '/api/auth',
        json={'username': 'test', 'password': 'password_for_test', 'token': '999999'}
    )
    assert resp.status_code == 401
    assert json.loads(resp.data.decode('utf8')).get('message') == 'Invalid credentials'


def test_authentication_without_activation(app, client):
    utils = Utils(app, client)
    utils.create_user(username='random', password='password_for_random', verified=False)
    resp = client.post('/api/auth', json={'username': 'random', 'password': 'password_for_random'})
    assert resp.status_code == 401
    assert json.loads(resp.data.decode('utf8')).get('message') == 'Account not activated'


def test_get_user_info(app, client):
    utils = Utils(app, client)
    resp = client.get('/api/auth', headers={'Authorization': f'Bearer {utils.generate_access_token()}'})
    assert resp.status_code == 200
    assert 'username' in json.loads(resp.data.decode()).get('data')
    assert parser.parse(json.loads(resp.data.decode()).get('data').get('created'))


def test_get_user_info_without_token(app, client):
    resp = client.get('/api/auth')
    assert resp.status_code == 401
    assert json.loads(resp.data.decode('utf8')).get('message') == 'Missing access token'


def test_get_user_info_invalid_token(app, client):
    resp = client.get('/api/auth', headers={'Authorization': 'Bearer invalid'})
    assert resp.status_code == 401
    assert json.loads(resp.data.decode('utf8')).get('message') == 'Invalid access token'


def test_refresh_token(app, client):
    utils = Utils(app, client)
    access_token, refresh_token = utils.generate_access_token(refresh=True)

    resp = client.get('/api/auth', headers={'Authorization': f'Bearer {access_token}'})
    assert resp.status_code == 200

    resp = client.post('/api/auth/refresh', json={'refreshToken': refresh_token})
    assert resp.status_code == 200
    assert json.loads(resp.data.decode()).get('message') == 'Token refresh was successful'
    assert 'accessToken' in json.loads(resp.data.decode())

    access_token = json.loads(resp.data.decode()).get('accessToken')
    resp = client.get('/api/auth', headers={'Authorization': f'Bearer {access_token}'})
    assert resp.status_code == 200


def test_refresh_token_wrong_data(app, client):
    utils = Utils(app, client)
    access_token, refresh_token = utils.generate_access_token(refresh=True)

    resp = client.get('/api/auth', headers={'Authorization': f'Bearer {access_token}'})
    assert resp.status_code == 200

    resp = client.post('/api/auth/refresh', json={'refreshToken': 'invalid'})
    assert resp.status_code == 401
    assert json.loads(resp.data.decode()).get('message') == 'Invalid refresh token'


def test_refresh_token_invalid_data(app, client):
    utils = Utils(app, client)
    access_token, refresh_token = utils.generate_access_token(refresh=True)

    resp = client.get('/api/auth', headers={'Authorization': f'Bearer {access_token}'})
    assert resp.status_code == 200

    resp = client.post('/api/auth/refresh', json={'invalid': 'invalid'})
    assert resp.status_code == 400
    assert json.loads(resp.data.decode()).get('message') == 'Payload is invalid'


def test_refresh_token_deleted_account(app, client):
    utils = Utils(app, client)
    access_token, refresh_token = utils.generate_access_token(refresh=True)

    resp = client.get('/api/auth', headers={'Authorization': f'Bearer {access_token}'})
    assert resp.status_code == 200

    utils.delete_user()

    resp = client.post('/api/auth/refresh', json={'refreshToken': refresh_token})
    assert resp.status_code == 400
    assert json.loads(resp.data.decode()).get('message') == 'User does not exist!'


def test_logout(app, client):
    utils = Utils(app, client)
    access_token, refresh_token = utils.generate_access_token(refresh=True)

    resp = client.get('/api/auth', headers={'Authorization': f'Bearer {access_token}'})
    assert resp.status_code == 200

    resp = client.delete(f'/api/auth/refresh/{refresh_token}')
    assert resp.status_code == 200
    assert json.loads(resp.data.decode()).get('data') == 'Successfully blacklisted token'

    # refresh token should now be invalid, access token will be still valid til it's expired
    resp = client.post('/api/auth/refresh', json={'refreshToken': refresh_token})
    assert resp.status_code == 401
    assert json.loads(resp.data.decode()).get('data') == 'Invalid refresh token'


def test_logout_invalid(app, client):
    utils = Utils(app, client)
    access_token, refresh_token = utils.generate_access_token(refresh=True)

    resp = client.get('/api/auth', headers={'Authorization': f'Bearer {access_token}'})
    assert resp.status_code == 200

    resp = client.delete('/api/auth/refresh/invalid')
    assert resp.status_code == 401
    assert json.loads(resp.data.decode()).get('message') == 'Invalid refresh token'


def test_logout_blacklisted(app, client):
    utils = Utils(app, client)
    access_token, refresh_token = utils.generate_admin_access_token(refresh=True)

    resp = client.get('/api/auth', headers={'Authorization': f'Bearer {access_token}'})
    assert resp.status_code == 200

    resp = client.delete(f'/api/auth/refresh/{refresh_token}')
    assert resp.status_code == 200
    assert json.loads(resp.data.decode()).get('data') == 'Successfully blacklisted token'

    resp = client.delete(f'/api/auth/refresh/{refresh_token}')
    assert resp.status_code == 401
    assert json.loads(resp.data.decode()).get('message') == 'Invalid refresh token'


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
