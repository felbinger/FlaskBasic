from app.api import User
import json
from hashlib import sha512
from .utils import create_dummy_user, create_dummy_admin, get_admin_token, get_user_token


# Admin: create user
def test_create_user(app, client):
    token = get_admin_token(app, client)
    data = {'username': 'qwerty',
            'password': 'i7Co8yvFWDGZfNMUQtcg',
            'email': 'test@test.com',
            'role': 'admin'}
    resp = client.post('/api/users', headers={'Access-Token': token}, json=data)
    assert resp.status_code == 201
    assert json.loads(resp.data.decode()).get('data').get('username') == data.get('username')
    assert json.loads(resp.data.decode()).get('data').get('role').get('name') == data.get('role')
    with app.app_context():
        user = User.query.filter_by(username=data.get('username')).first()
        assert user.password == sha512(data.get('password').encode('utf8')).hexdigest()


def test_create_user_error_role(app, client):
    token = get_admin_token(app, client)
    data = {'username': 'qwerty',
            'password': 'i7Co8yvFWDGZfNMUQtcg',
            'email': 'test@test.com',
            'role': 'invalid_role'}
    resp = client.post('/api/users', headers={'Access-Token': token}, json=data)
    assert resp.status_code == 404
    assert json.loads(resp.data.decode()).get('message') == 'Role does not exist!'


def test_create_two_equal_usernames(app, client):
    with app.app_context():
        token = get_admin_token(app, client)
        data = {'username': 'test',
                'password': 'i7Co8yvFWDGZfNMUQtcg',
            'email': 'test@test.com',
                'role': 'user'}
        resp = client.post('/api/users', headers={'Access-Token': token}, json=data)
        assert resp.status_code == 422
        assert json.loads(resp.data.decode()).get('message') == 'Username already in use!'


def test_create_user_without_data(app, client):
    token = get_admin_token(app, client)
    resp = client.post('/api/users', headers={'Access-Token': token})
    assert resp.status_code == 400
    assert json.loads(resp.data.decode()).get('message') == "Payload is invalid"


def test_create_user_invalid_data(app, client):
    token = get_admin_token(app, client)
    data = {'name': 'something'}
    resp = client.post('/api/users', headers={'Access-Token': token}, json=data)
    assert resp.status_code == 400
    assert json.loads(resp.data.decode()).get('message') == "Payload is invalid"


def test_create_user_as_user(app, client):
    token = get_user_token(app, client)
    data = {'username': 'qwerty',
            'password': 'i7Co8yvFWDGZfNMUQtcg',
            'email': 'test@test.com',
            'role': 'user'}
    resp = client.post('/api/users', headers={'Access-Token': token}, json=data)
    assert resp.status_code == 403
    assert json.loads(resp.data.decode()).get('message') == 'Access Denied!'


# Admin: get user by publicId
def test_get_user(app, client):
    with app.app_context():
        user_id = create_dummy_admin(app=app, client=client, name='john')
        resp = client.get(f'/api/users/{user_id}', headers={'Access-Token': get_admin_token(app, client)})
        assert resp.status_code == 200
        assert json.loads(resp.data.decode()).get('data').get('publicId') == user_id


def test_get_invalid_user(app, client):
    resp = client.get(f'/api/users/fake_user_id', headers={'Access-Token': get_admin_token(app, client)})
    assert resp.status_code == 404
    assert json.loads(resp.data.decode()).get('message') == 'User does not exist!'


# Admin: get all users
def test_get_all_user(app, client):
    with app.app_context():
        create_dummy_admin(app=app, client=client, name='jane')
        resp = client.get('/api/users', headers={'Access-Token': get_admin_token(app, client)})
        assert resp.status_code == 200
        assert len(json.loads(resp.data.decode()).get('data')) == len(User.query.all())


# update user (identified by /me)
def test_self_update(app, client):
    token = get_admin_token(app, client)
    json_data = {'username': 'new'}
    resp = client.put(f'/api/users/me', headers={'Access-Token': token}, json=json_data)
    assert resp.status_code == 200
    assert json.loads(resp.data.decode()).get('data').get('username') == json_data.get('username')


def test_self_update_not_allowed_change_role(app, client):
    json_data = {'role': 'admin'}
    resp = client.put(f'/api/users/me', headers={'Access-Token': get_user_token(app, client)}, json=json_data)
    assert resp.status_code == 403
    assert json.loads(resp.data.decode()).get('message') == 'You are not allowed to change your role!'


# Admin: update user (identified by publicId)
def test_admin_update(app, client):
    with app.app_context():
        user_id = create_dummy_admin(app=app, client=client)
        json_data = {'role': 'admin'}
        resp = client.put(f'/api/users/{user_id}', headers={'Access-Token': get_admin_token(app, client)}, json=json_data)
        assert resp.status_code == 200
        assert json.loads(resp.data.decode()).get('data').get('role').get('description') == 'Administrator'


def test_admin_update_invalid_user(app, client):
    with app.app_context():
        create_dummy_user(app=app, client=client)
        json_data = {'roel': 'admin'}
        resp = client.put(f'/api/users/doof', headers={'Access-Token': get_admin_token(app, client)}, json=json_data)
        assert resp.status_code == 404
        assert json.loads(resp.data.decode()).get('message') == 'User does not exist'


# Admin: delete user (identified by publicId)
def test_delete_user(app, client):
    with app.app_context():
        user_id = create_dummy_admin(app=app, client=client)
        resp = client.delete(f'/api/users/{user_id}', headers={'Access-Token': get_admin_token(app, client)})
        assert resp.status_code == 200
