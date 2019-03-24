from app.api import Role, User
import json
from .utils import get_admin_token, create_dummy_role


# admin: create role
def test_create_role(app, client):
    with app.app_context():
        token = get_admin_token(app, client)
        data = {'name': 'test_role', 'description': 'test_role_description'}
        resp = client.post('/api/roles', headers={'Access-Token': token}, json=data)
        assert resp.status_code == 201
        assert json.loads(resp.data.decode()).get('data').get('name') == data.get('name')
        assert json.loads(resp.data.decode()).get('data').get('description') == data.get('description')


def test_create_role_without_data(app, client):
    with app.app_context():
        token = get_admin_token(app, client)
        resp = client.post('/api/roles', headers={'Access-Token': token})
        assert resp.status_code == 400
        assert json.loads(resp.data.decode()).get('message') == 'Payload is invalid'


def test_create_role_invalid_data(app, client):
    with app.app_context():
        token = get_admin_token(app, client)
        data = {'name': 'something'}
        resp = client.post('/api/roles', headers={'Access-Token': token}, json=data)
        assert resp.status_code == 400
        assert json.loads(resp.data.decode()).get('message') == 'Payload is invalid'


# get all roles
def test_get_all_roles(app, client):
    with app.app_context():
        create_dummy_role(app=app, client=client, name='support')
        create_dummy_role(app=app, client=client, name='user')
        token = get_admin_token(app, client)
        resp = client.get('/api/roles', headers={'Access-Token': token})
        assert resp.status_code == 200
        with app.app_context():
            assert len(json.loads(resp.data.decode()).get('data')) == len(Role.query.all())


# get role by name
def test_get_role(app, client):
    with app.app_context():
        create_dummy_role(app=app, client=client, name='support')
        resp = client.get(f'/api/roles/support', headers={'Access-Token': get_admin_token(app, client)})
        assert resp.status_code == 200
        assert json.loads(resp.data.decode()).get('data').get('description') == 'test'


def test_get_role_invalid_role(app, client):
    with app.app_context():
        create_dummy_role(app=app, client=client, name='support')
        resp = client.get(f'/api/roles/invalid_role', headers={'Access-Token': get_admin_token(app, client)})
        assert resp.status_code == 404
        assert json.loads(resp.data.decode()).get('message') == 'Role does not exist!'


# admin update role
def test_update_role(app, client):
    with app.app_context():
        create_dummy_role(app=app, client=client, name='support')
        json_data = {'description': 'new description'}
        resp = client.put(f'/api/roles/support', headers={'Access-Token': get_admin_token(app, client)}, json=json_data)
        assert resp.status_code == 200
        assert json.loads(resp.data.decode()).get('data').get('description') == 'new description'


def test_update_role_invalid_role(app, client):
    with app.app_context():
        json_data = {'description': 'new description'}
        resp = client.put(f'/api/roles/afk', headers={'Access-Token': get_admin_token(app, client)}, json=json_data)
        assert resp.status_code == 404
        assert json.loads(resp.data.decode()).get('message') == 'Role does not exist!'


def test_update_role_invalid_data(app, client):
    with app.app_context():
        create_dummy_role(app=app, client=client, name='abc')
        json_data = {'a': '1'}
        resp = client.put(f'/api/roles/abc', headers={'Access-Token': get_admin_token(app, client)}, json=json_data)
        assert resp.status_code == 400
        assert json.loads(resp.data.decode()).get('message') == 'Payload is invalid'


def test_delete_role(app, client):
    with app.app_context():
        create_dummy_role(app=app, client=client, name='support')
        resp = client.delete(f'/api/roles/support', headers={'Access-Token': get_admin_token(app, client)})
        assert resp.status_code == 200
