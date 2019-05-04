from tests.utils import Utils

import json


def test_create(app, client):
    utils = Utils(app, client)

    data = {'name': 'test_role', 'description': 'test_role_description'}
    headers = {'Authorization': f'Bearer {utils.generate_admin_access_token()}'}
    resp = client.post('/api/roles', headers=headers, json=data)
    assert resp.status_code == 201
    assert json.loads(resp.data.decode()).get('data').get('name') == data.get('name')
    assert json.loads(resp.data.decode()).get('data').get('description') == data.get('description')


def test_create_without_data(app, client):
    utils = Utils(app, client)
    headers = {'Authorization': f'Bearer {utils.generate_admin_access_token()}'}
    resp = client.post('/api/roles', headers=headers)
    assert resp.status_code == 400
    assert json.loads(resp.data.decode()).get('message') == 'Payload is invalid'


def test_create_invalid_data(app, client):
    data = {'invalid': 'invalid'}
    utils = Utils(app, client)
    headers = {'Authorization': f'Bearer {utils.generate_admin_access_token()}'}
    resp = client.post('/api/roles', headers=headers, json=data)
    assert resp.status_code == 400
    assert json.loads(resp.data.decode()).get('message') == 'Payload is invalid'


def test_create_existing(app, client):
    utils = Utils(app, client)

    data = {'name': 'admin', 'description': 'test_role_description'}
    headers = {'Authorization': f'Bearer {utils.generate_admin_access_token()}'}
    resp = client.post('/api/roles', headers=headers, json=data)
    assert resp.status_code == 400
    assert json.loads(resp.data.decode()).get('message') == 'Name already in use!'


def test_update(app, client):
    utils = Utils(app, client)

    data = {'description': 'Not the real description of admin!'}
    headers = {'Authorization': f'Bearer {utils.generate_admin_access_token()}'}
    resp = client.put(f'/api/roles/admin', headers=headers, json=data)
    assert resp.status_code == 200
    assert json.loads(resp.data.decode()).get('data').get('description') == data.get('description')


def test_update_without_data(app, client):
    utils = Utils(app, client)

    headers = {'Authorization': f'Bearer {utils.generate_admin_access_token()}'}
    resp = client.put(f'/api/roles/admin', headers=headers)
    assert resp.status_code == 400
    assert json.loads(resp.data.decode()).get('message') == 'Payload is invalid'


def test_update_invalid_data(app, client):
    utils = Utils(app, client)

    headers = {'Authorization': f'Bearer {utils.generate_admin_access_token()}'}
    resp = client.put(f'/api/roles/admin', headers=headers, json={'invalid': 'invalid'})
    assert resp.status_code == 400
    assert json.loads(resp.data.decode()).get('message') == 'Payload is invalid'


def test_update_non_existing(app, client):
    utils = Utils(app, client)

    data = {'description': 'Not the real description of admin!'}
    headers = {'Authorization': f'Bearer {utils.generate_admin_access_token()}'}
    resp = client.put(f'/api/roles/invalid', headers=headers, json=data)
    assert resp.status_code == 404
    assert json.loads(resp.data.decode()).get('message') == 'Role does not exist!'


def test_delete(app, client):
    utils = Utils(app, client)

    # create role to delete
    data = {'name': 'test_role', 'description': 'test_role_description'}
    headers = {'Authorization': f'Bearer {utils.generate_admin_access_token()}'}
    resp = client.post('/api/roles', headers=headers, json=data)
    assert resp.status_code == 201

    resp = client.delete(f'/api/roles/test_role', headers=headers)
    assert resp.status_code == 200
    assert json.loads(resp.data.decode()).get('data') == 'Successfully deleted role!'


def test_delete_without_data(app, client):
    utils = Utils(app, client)
    headers = {'Authorization': f'Bearer {utils.generate_admin_access_token()}'}
    resp = client.delete(f'/api/roles', headers=headers)
    assert resp.status_code == 405


def test_delete_invalid_data(app, client):
    utils = Utils(app, client)
    headers = {'Authorization': f'Bearer {utils.generate_admin_access_token()}'}
    resp = client.delete(f'/api/roles/invalid', headers=headers)
    assert resp.status_code == 404


def test_delete_in_use(app, client):
    utils = Utils(app, client)
    access_token = utils.generate_admin_access_token()

    # create role that can be deleted
    data = {'name': 'test_role', 'description': 'test_role_description'}
    headers = {'Authorization': f'Bearer {access_token}'}
    resp = client.post('/api/roles', headers=headers, json=data)
    assert resp.status_code == 201

    # create a user that has this role
    data = {
        'username': 'new_user',
        'password': 'password_for_new_user',
        'email': 'new_user@test.test',
        'role': 'test_role'
    }
    headers = {'Authorization': f'Bearer {access_token}'}
    resp = client.post('/api/users', headers=headers, json=data)
    assert resp.status_code == 201

    headers = {'Authorization': f'Bearer {access_token}'}
    resp = client.delete(f'/api/roles/test_role', headers=headers)
    assert resp.status_code == 422


def test_delete_user(app, client):
    utils = Utils(app, client)
    headers = {'Authorization': f'Bearer {utils.generate_admin_access_token()}'}
    resp = client.delete(f'/api/roles/user', headers=headers)
    assert resp.status_code == 422


def test_delete_admin(app, client):
    utils = Utils(app, client)
    headers = {'Authorization': f'Bearer {utils.generate_admin_access_token()}'}
    resp = client.delete(f'/api/roles/admin', headers=headers)
    assert resp.status_code == 422


def test_get(app, client):
    utils = Utils(app, client)
    headers = {'Authorization': f'Bearer {utils.generate_admin_access_token()}'}
    resp = client.get(f'/api/roles/user', headers=headers)
    assert resp.status_code == 200
    assert json.loads(resp.data.decode()).get('data').get('description') == 'User'


def test_get_invalid(app, client):
    utils = Utils(app, client)
    headers = {'Authorization': f'Bearer {utils.generate_admin_access_token()}'}
    resp = client.get(f'/api/roles/invalid', headers=headers)
    assert resp.status_code == 404


def test_get_all(app, client):
    utils = Utils(app, client)
    headers = {'Authorization': f'Bearer {utils.generate_admin_access_token()}'}
    resp = client.get(f'/api/roles', headers=headers)
    assert resp.status_code == 200
    assert len(json.loads(resp.data.decode()).get('data')) == 2
