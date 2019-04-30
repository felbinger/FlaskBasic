from tests.utils import Utils

import json


def test_create(app, client):
    utils = Utils(app, client)

    data = {
        'username': 'new_user',
        'password': 'password_for_new_user',
        'email': 'new_user@test.test',
        'role': 'user'
    }
    headers = {'Authorization': f'Bearer {utils.generate_admin_access_token()}'}
    resp = client.post('/api/users', headers=headers, json=data)
    assert resp.status_code == 201
    assert json.loads(resp.data.decode()).get('data').get('name') == data.get('name')
    assert json.loads(resp.data.decode()).get('data').get('description') == data.get('description')


def test_create_without_permissions(app, client):
    utils = Utils(app, client)

    data = {
        'username': 'new_user',
        'password': 'password_for_new_user',
        'email': 'new_user@test.test',
        'role': 'user'
    }
    headers = {'Authorization': f'Bearer {utils.generate_access_token()}'}
    resp = client.post('/api/users', headers=headers, json=data)
    assert resp.status_code == 403
    assert json.loads(resp.data.decode()).get('message') == 'Access Denied!'


def test_create_without_data(app, client):
    utils = Utils(app, client)
    headers = {'Authorization': f'Bearer {utils.generate_admin_access_token()}'}
    resp = client.post('/api/users', headers=headers)
    assert resp.status_code == 400
    assert json.loads(resp.data.decode()).get('message') == 'Payload is invalid'


def test_create_invalid_data(app, client):
    data = {'invalid': 'invalid'}
    utils = Utils(app, client)
    headers = {'Authorization': f'Bearer {utils.generate_admin_access_token()}'}
    resp = client.post('/api/users', headers=headers, json=data)
    assert resp.status_code == 400
    assert json.loads(resp.data.decode()).get('message') == 'Payload is invalid'


def test_create_invalid_role(app, client):
    utils = Utils(app, client)

    data = {
        'username': 'new_user',
        'password': 'password_for_new_user',
        'email': 'new_user@test.test',
        'role': 'invalid'
    }
    headers = {'Authorization': f'Bearer {utils.generate_admin_access_token()}'}
    resp = client.post('/api/users', headers=headers, json=data)
    assert resp.status_code == 404
    assert json.loads(resp.data.decode()).get('message') == 'Role does not exist!'


def test_create_equal_usernames(app, client):
    utils = Utils(app, client)

    data = {
        'username': 'test',
        'password': 'password_for_new_user',
        'email': 'new_user@test.test',
        'role': 'invalid'
    }
    headers = {'Authorization': f'Bearer {utils.generate_admin_access_token()}'}
    resp = client.post('/api/users', headers=headers, json=data)
    assert resp.status_code == 422
    assert json.loads(resp.data.decode()).get('message') == 'Username already in use!'


def test_admin_update(app, client):
    utils = Utils(app, client)
    public_id = utils.get_public_id()

    data = {'displayName': 'My new display name!'}
    headers = {'Authorization': f'Bearer {utils.generate_admin_access_token()}'}
    resp = client.put(f'/api/users/{public_id}', headers=headers, json=data)
    assert resp.status_code == 200
    assert json.loads(resp.data.decode()).get('data').get('displayName') == data.get('displayName')


def test_admin_update_without_data(app, client):
    utils = Utils(app, client)
    public_id = utils.get_public_id()

    headers = {'Authorization': f'Bearer {utils.generate_admin_access_token()}'}
    resp = client.put(f'/api/users/{public_id}', headers=headers)
    assert resp.status_code == 400


def test_admin_update_invalid_data(app, client):
    utils = Utils(app, client)
    public_id = utils.get_public_id()

    headers = {'Authorization': f'Bearer {utils.generate_admin_access_token()}'}
    resp = client.put(f'/api/users/{public_id}', headers=headers, json={'invalid': 'invalid'})
    assert resp.status_code == 400


def test_update(app, client):
    utils = Utils(app, client)

    data = {'displayName': 'My new display name!'}
    headers = {'Authorization': f'Bearer {utils.generate_admin_access_token()}'}
    resp = client.put('/api/users/me', headers=headers, json=data)
    assert resp.status_code == 200
    assert json.loads(resp.data.decode()).get('data').get('displayName') == data.get('displayName')


def test_update_without_data(app, client):
    utils = Utils(app, client)

    headers = {'Authorization': f'Bearer {utils.generate_admin_access_token()}'}
    resp = client.put('/api/users/me', headers=headers)
    assert resp.status_code == 400


def test_update_invalid_data(app, client):
    utils = Utils(app, client)

    headers = {'Authorization': f'Bearer {utils.generate_admin_access_token()}'}
    resp = client.put('/api/users/me', headers=headers, json={'invalid': 'invalid'})
    assert resp.status_code == 400


def test_delete(app, client):
    utils = Utils(app, client)

    # create user to delete
    data = {
        'username': 'new_user',
        'password': 'password_for_new_user',
        'email': 'new_user@test.test',
        'role': 'user'
    }
    headers = {'Authorization': f'Bearer {utils.generate_admin_access_token()}'}
    resp = client.post('/api/users', headers=headers, json=data)
    assert resp.status_code == 201

    public_id = utils.get_public_id('new_user')

    resp = client.delete(f'/api/users/{public_id}', headers=headers)
    assert resp.status_code == 200
    assert json.loads(resp.data.decode()).get('data') == 'Successfully deleted user!'


def test_delete_without_data(app, client):
    utils = Utils(app, client)
    headers = {'Authorization': f'Bearer {utils.generate_admin_access_token()}'}
    resp = client.delete(f'/api/users', headers=headers)
    assert resp.status_code == 405


def test_delete_invalid_data(app, client):
    utils = Utils(app, client)
    headers = {'Authorization': f'Bearer {utils.generate_admin_access_token()}'}
    resp = client.delete(f'/api/users/invalid', headers=headers)
    assert resp.status_code == 404
    assert json.loads(resp.data.decode()).get('message') == 'User does not exist'


def test_delete_without_permissions(app, client):
    utils = Utils(app, client)
    public_id = utils.get_public_id()

    headers = {'Authorization': f'Bearer {utils.generate_access_token()}'}
    resp = client.delete(f'/api/users/{public_id}', headers=headers)
    assert resp.status_code == 403
    assert json.loads(resp.data.decode()).get('message') == 'Access Denied!'


def test_get(app, client):
    utils = Utils(app, client)
    public_id = utils.get_public_id()
    headers = {'Authorization': f'Bearer {utils.generate_admin_access_token()}'}
    resp = client.get(f'/api/users/{public_id}', headers=headers)
    assert resp.status_code == 200
    assert json.loads(resp.data.decode()).get('data').get('email') == 'test@example.com'
    assert json.loads(resp.data.decode()).get('data').get('displayName') == 'test'
    assert not json.loads(resp.data.decode()).get('data').get('2fa')


def test_get_invalid(app, client):
    utils = Utils(app, client)
    headers = {'Authorization': f'Bearer {utils.generate_admin_access_token()}'}
    resp = client.get(f'/api/users/invalid', headers=headers)
    assert resp.status_code == 404


def test_get_all(app, client):
    utils = Utils(app, client)
    headers = {'Authorization': f'Bearer {utils.generate_admin_access_token()}'}
    resp = client.get(f'/api/users', headers=headers)
    assert resp.status_code == 200


def test_get_all_without_permissions(app, client):
    utils = Utils(app, client)
    headers = {'Authorization': f'Bearer {utils.generate_access_token()}'}
    resp = client.get(f'/api/users', headers=headers)
    assert resp.status_code == 403
    assert json.loads(resp.data.decode()).get('message') == 'Access Denied!'
