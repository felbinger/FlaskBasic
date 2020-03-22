from tests.utils import Utils

import json
import onetimepass


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
    assert resp.status_code == 200


def test_admin_update_invalid_data(app, client):
    utils = Utils(app, client)
    public_id = utils.get_public_id()

    headers = {'Authorization': f'Bearer {utils.generate_admin_access_token()}'}
    resp = client.put(f'/api/users/{public_id}', headers=headers, json={'invalid': 'invalid'})
    assert resp.status_code == 400


def test_admin_update_non_existing_role(app, client):
    utils = Utils(app, client)
    public_id = utils.get_public_id()

    headers = {'Authorization': f'Bearer {utils.generate_admin_access_token()}'}
    resp = client.put(f'/api/users/{public_id}', headers=headers, json={'role': 'invalid'})
    assert resp.status_code == 400
    assert json.loads(resp.data.decode()).get('message') == 'Invalid Role'


def test_admin_update_invalid_user(app, client):
    utils = Utils(app, client)

    headers = {'Authorization': f'Bearer {utils.generate_admin_access_token()}'}
    resp = client.put(f'/api/users/invalid', headers=headers, json={'displayName': 'new'})
    assert resp.status_code == 404
    assert json.loads(resp.data.decode()).get('message') == 'User does not exist'


def test_admin_update_enable_2fa(app, client):
    utils = Utils(app, client)
    public_id = utils.get_public_id()

    headers = {'Authorization': f'Bearer {utils.generate_admin_access_token()}'}
    resp = client.put(f'/api/users/{public_id}', headers=headers, json={'totp_enabled': True})
    assert resp.status_code == 400
    assert json.loads(resp.data.decode()).get('message') == 'You are not allowed to enable 2FA.'


def test_admin_update_disable_2fa(app, client):
    utils = Utils(app, client)
    utils.enable_2fa()
    public_id = utils.get_public_id()

    headers = {'Authorization': f'Bearer {utils.generate_admin_access_token()}'}

    # check if 2fa is enabled
    resp = client.get(f'/api/users/{public_id}', headers=headers)
    assert json.loads(resp.data.decode()).get('data').get('2fa')

    # disable 2fa
    resp = client.put(f'/api/users/{public_id}', headers=headers, json={'totp_enabled': False})
    assert resp.status_code == 200
    assert not json.loads(resp.data.decode()).get('data').get('2fa')


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
    assert resp.status_code == 200


def test_update_invalid_data(app, client):
    utils = Utils(app, client)

    headers = {'Authorization': f'Bearer {utils.generate_admin_access_token()}'}
    resp = client.put('/api/users/me', headers=headers, json={'invalid': 'invalid'})
    assert resp.status_code == 400


def test_update_enable_2fa(app, client):
    utils = Utils(app, client)

    headers = {'Authorization': f'Bearer {utils.generate_admin_access_token()}'}
    # first step to enable 2fa, get secret key
    resp = client.put('/api/users/me', headers=headers, json={'totp_enabled': True})
    assert resp.status_code == 200
    print(resp.data.decode())
    assert not json.loads(resp.data.decode()).get('data').get('2fa')
    assert '2fa_secret' in json.loads(resp.data.decode()).get('data')
    secret = json.loads(resp.data.decode()).get('data').get('2fa_secret')

    # get the qr code
    resp = client.get('/api/users/2fa', headers=headers)
    assert resp.status_code == 200
    # todo check if svg in resp.data.decode()

    # generate a 2fa token using the secret key, and use it to activate 2fa
    totp_token = str(onetimepass.get_totp(secret)).zfill(6)
    resp = client.post('/api/users/2fa', headers=headers, json={'token': str(totp_token)})
    assert resp.status_code == 200
    assert json.loads(resp.data.decode()).get('message') == '2fa has been enabled'


def test_update_enable_2fa_invalid_data(app, client):
    utils = Utils(app, client)

    headers = {'Authorization': f'Bearer {utils.generate_admin_access_token()}'}
    # first step to enable 2fa, get secret key
    resp = client.put('/api/users/me', headers=headers, json={'totp_enabled': True})
    assert resp.status_code == 200
    assert not json.loads(resp.data.decode()).get('data').get('2fa')
    assert '2fa_secret' in json.loads(resp.data.decode()).get('data')
    secret = json.loads(resp.data.decode()).get('data').get('2fa_secret')

    # generate a 2fa token using the secret key, and use it to activate 2fa
    totp_token = str(onetimepass.get_totp(secret)).zfill(6)
    resp = client.post('/api/users/2fa', headers=headers, json={'invalid': str(totp_token)})
    assert resp.status_code == 400
    assert json.loads(resp.data.decode()).get('message') == 'Payload is invalid'


def test_update_enable_2fa_invalid_token(app, client):
    utils = Utils(app, client)

    headers = {'Authorization': f'Bearer {utils.generate_admin_access_token()}'}
    # first step to enable 2fa, get secret key
    resp = client.put('/api/users/me', headers=headers, json={'totp_enabled': True})
    assert resp.status_code == 200
    assert not json.loads(resp.data.decode()).get('data').get('2fa')
    assert '2fa_secret' in json.loads(resp.data.decode()).get('data')
    secret = json.loads(resp.data.decode()).get('data').get('2fa_secret')

    # generate a 2fa token using the secret key, and use it to activate 2fa
    totp_token = str(onetimepass.get_totp(secret)).zfill(6)
    resp = client.post('/api/users/2fa', headers=headers, json={'token': '000000'})
    assert resp.status_code == 400
    assert json.loads(resp.data.decode()).get('message') == 'invalid token, try again'

    resp = client.post('/api/users/2fa', headers=headers, json={'token': str(totp_token)})
    assert resp.status_code == 200
    assert json.loads(resp.data.decode()).get('message') == '2fa has been enabled'


def test_update_enable_2fa_only_stage_2(app, client):
    utils = Utils(app, client)

    headers = {'Authorization': f'Bearer {utils.generate_admin_access_token()}'}

    # generate a 2fa token using the secret key, and use it to activate 2fa
    resp = client.post('/api/users/2fa', headers=headers, json={'token': '000000'})
    assert resp.status_code == 400
    assert json.loads(resp.data.decode()).get('message') == '2fa is not setted up'


def test_update_show_qr_after_2fa_has_been_enabled(app, client):
    utils = Utils(app, client)

    headers = {'Authorization': f'Bearer {utils.generate_admin_access_token()}'}
    # first step to enable 2fa, get secret key
    resp = client.put('/api/users/me', headers=headers, json={'totp_enabled': True})
    assert resp.status_code == 200
    assert not json.loads(resp.data.decode()).get('data').get('2fa')
    assert '2fa_secret' in json.loads(resp.data.decode()).get('data')

    # generate a 2fa token using the secret key, and use it to activate 2fa
    secret = json.loads(resp.data.decode()).get('data').get('2fa_secret')
    totp_token = str(onetimepass.get_totp(secret)).zfill(6)
    resp = client.post('/api/users/2fa', headers=headers, json={'token': str(totp_token)})
    assert resp.status_code == 200
    assert json.loads(resp.data.decode()).get('message') == '2fa has been enabled'

    # it should not be possible to generate the qr code after 2fa has been enabled
    # this would be a potential security vulnerability
    resp = client.get('/api/users/2fa', headers=headers)
    assert resp.status_code == 400
    assert json.loads(resp.data.decode()).get('message') == 'Unable to generate QR Code'


def test_update_disable_2fa(app, client):
    utils = Utils(app, client)
    utils.enable_2fa()

    headers = {'Authorization': f'Bearer {utils.generate_access_token()}'}

    # check if 2fa is enabled
    # resp = client.get('/api/auth', headers=headers)
    resp = client.get('/api/auth', headers={'Authorization': f'Bearer {utils.generate_access_token()}'})
    assert json.loads(resp.data.decode()).get('data').get('2fa')

    # disable 2fa
    resp = client.put(
        f'/api/users/me',
        headers=headers,
        json={'totp_enabled': False, 'totp_token': utils.generate_2fa_token()}
    )
    assert resp.status_code == 200
    assert not json.loads(resp.data.decode()).get('data').get('2fa')


def test_update_disable_2fa_without_token(app, client):
    utils = Utils(app, client)
    utils.enable_2fa()

    headers = {'Authorization': f'Bearer {utils.generate_access_token()}'}

    # check if 2fa is enabled
    # resp = client.get('/api/auth', headers=headers)
    resp = client.get('/api/auth', headers={'Authorization': f'Bearer {utils.generate_access_token()}'})
    assert json.loads(resp.data.decode()).get('data').get('2fa')

    # disable 2fa
    resp = client.put(
        f'/api/users/me',
        headers=headers,
        json={'totp_enabled': False}
    )
    assert resp.status_code == 400
    assert json.loads(resp.data.decode()).get('message') == 'Unable to deactivate 2fa, token not submitted'


def test_update_disable_2fa_invalid_token(app, client):
    utils = Utils(app, client)
    utils.enable_2fa()

    headers = {'Authorization': f'Bearer {utils.generate_access_token()}'}

    # check if 2fa is enabled
    # resp = client.get('/api/auth', headers=headers)
    resp = client.get('/api/auth', headers={'Authorization': f'Bearer {utils.generate_access_token()}'})
    assert json.loads(resp.data.decode()).get('data').get('2fa')

    # disable 2fa
    resp = client.put(
        f'/api/users/me',
        headers=headers,
        json={'totp_enabled': False, 'totp_token': '000000'}
    )
    assert resp.status_code == 400
    assert json.loads(resp.data.decode()).get('message') == 'Unable to deactivate 2fa, token is invalid'


def test_update_modify_role(app, client):
    utils = Utils(app, client)

    data = {'role': 'admin'}
    headers = {'Authorization': f'Bearer {utils.generate_access_token()}'}
    resp = client.put('/api/users/me', headers=headers, json=data)
    assert resp.status_code == 403
    assert json.loads(resp.data.decode()).get('message') == 'You are not allowed to change your role!'


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
