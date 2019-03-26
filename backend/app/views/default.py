from flask import Blueprint, render_template, request, session, redirect, url_for, flash
import requests

from .utils import require_login, require_logout, require_admin

default = Blueprint(__name__, 'default')


@default.route('/')
@require_login
def index():
    role = requests.get(
        f'{request.scheme}://{request.host}{url_for("auth_api")}',
        headers={'Access-Token': session.get('Access-Token')},
    ).json().get('data').get('role').get('name')
    return render_template('index.html', role=role)


@default.route('/login', methods=['GET', 'POST'])
@require_logout
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username and password:
            resp = requests.post(
                f'{request.scheme}://{request.host}{url_for("auth_api")}',
                json={
                    'username': username,
                    'password': password
                }
            ).json()
            if resp.get('token'):
                session['Access-Token'] = resp.get('token')
                return redirect(url_for('app.views.default.index'))
            else:
                flash(resp.get('message'), 'danger')
        else:
            flash('Missing credentials')
    return render_template('login.html')


@require_login
@default.route('/logout')
def logout():
    # todo contact redis server to make token invalid
    session['Access-Token'] = None
    return redirect(url_for('app.views.default.login'), code=302)


@default.route('/verify/<token>')
def verify(token):
    return requests.put(
        f'{request.scheme}://{request.host}{url_for("verify_mail_api", token=token)}'
    ).json().get('message')


@require_login
@default.route('/profile/<string:public_id>', methods=['GET', 'POST'])
def account(public_id):
    header = {'Access-Token': session.get('Access-Token')}
    if request.method == 'POST':
        if request.form is not None:
            action = request.form.get('action')

            if action == 'modifyProfile':
                public_id = request.form.get('id')
                if public_id:
                    resp = requests.put(
                        f'{request.scheme}://{request.host}{url_for("user_api")}/{public_id}',
                        json={
                            'displayName': request.form.get('displayName'),
                            'email': request.form.get('email')
                        },
                        headers=header
                    )
                    if resp.status_code != 200:
                        flash(f'Unable to update account: {resp.json().get("message")}', 'danger')
                    else:
                        flash('Account has been update!', 'success')
                else:
                    flash('You need to provide an uuid to update an account!', 'danger')

            elif action == 'changePassword':
                public_id = request.form.get('id')
                password = request.form.get('password')
                if public_id:
                    if password == request.form.get('password2'):
                        if len(password) < 8:
                            flash('Password is too short!', 'danger')
                        else:
                            resp = requests.put(
                                f'{request.scheme}://{request.host}{url_for("user_api")}/{public_id}',
                                headers=header,
                                json={
                                    'password': password
                                }
                            )
                            if resp.status_code != 200:
                                flash(f'Unable to update password: {resp.json().get("message")}', 'danger')
                            else:
                                flash('Password has been updated!', 'success')
                    else:
                        flash('The entered Password\'s are not the same!', 'danger')
                else:
                    flash('You need to provide an uuid to change the password of an account!', 'danger')

    role = requests.get(
        f'{request.scheme}://{request.host}{url_for("auth_api")}',
        headers={'Access-Token': session.get('Access-Token')},
    ).json().get('data').get('role').get('name')

    if public_id == 'me':
        data = requests.get(
            f'{request.scheme}://{request.host}{url_for("auth_api")}',
            headers=header,
        ).json().get('data')
    else:
        # requires admin privileges
        data = requests.get(
            f'{request.scheme}://{request.host}{url_for("user_api")}/{public_id}',
            headers=header,
        ).json().get('data')

    return render_template('profile.html', data=data, role=role)


@require_login
@require_admin
@default.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    header = {'Access-Token': session.get('Access-Token')}
    if request.method == 'POST':
        if request.form is not None:
            action = request.form.get('action')

            if action == 'createAccount':
                username = request.form.get('username')
                email = request.form.get('email')
                password = request.form.get('password')
                role = request.form.get('role')

                if not username or not email or not password or not role:
                    flash('Unable to create account! Make sure all boxes filled out!', 'danger')
                else:
                    if len(password) < 8:
                        flash('Password is too short!', 'danger')
                    else:
                        resp = requests.post(
                            f'{request.scheme}://{request.host}{url_for("user_api")}',
                            headers=header,
                            json={
                                'username': username,
                                'email': email,
                                'password': password,
                                'role': role
                            }
                        )
                        if resp.status_code != 201:
                            msg = resp.json().get("message")
                            flash(f'Unable to create account: {msg}', 'danger')
                        else:
                            flash('Account has been created successfully!', 'success')

            elif action == 'modifyAccount':
                public_id = request.form.get('id')
                if public_id:
                    resp = requests.put(
                        f'{request.scheme}://{request.host}{url_for("user_api")}/{public_id}',
                        json={
                            'username': request.form.get('username'),
                            'displayName': request.form.get('displayName'),
                            'email': request.form.get('email'),
                            'role': request.form.get('role')
                        },
                        headers=header
                    )
                    if resp.status_code != 200:
                        flash(f'Unable to update account: {resp.json().get("message")}', 'danger')
                    else:
                        flash('Account has been update!', 'success')
                else:
                    flash('You need to provide an uuid to update an account!', 'danger')

            elif action == 'changePassword':
                public_id = request.form.get('id')
                password = request.form.get('password')
                if public_id:
                    if password == request.form.get('password2'):
                        if len(password) < 8:
                            flash('Password is too short!', 'danger')
                        else:
                            resp = requests.put(
                                f'{request.scheme}://{request.host}{url_for("user_api")}/{public_id}',
                                headers=header,
                                json={
                                    'password': password
                                }
                            )
                            if resp.status_code != 200:
                                flash(f'Unable to update password: {resp.json().get("message")}', 'danger')
                            else:
                                flash('Password has been updated!', 'success')
                    else:
                        flash('The entered Password\'s are not the same!', 'danger')
                else:
                    flash('You need to provide an uuid to change the password of an account!', 'danger')

            elif action == 'deleteAccount':
                public_id = request.form.get('id')
                if public_id:
                    resp = requests.delete(
                        f'{request.scheme}://{request.host}{url_for("user_api")}/{public_id}',
                        headers=header
                    )
                    if resp.status_code != 200:
                        flash(f'Unable to delete account: {resp.json().get("message")}', 'danger')
                    else:
                        flash('Account has been deleted!', 'success')
                else:
                    flash('You need to provide an uuid to delete an account!', 'danger')

            elif action == 'createRole':
                name = request.form.get('name')
                description = request.form.get('description')
                if not name or not description:
                    flash('Unable to create Role: Name and description cannot be emtpy!', 'danger')
                else:
                    resp = requests.post(
                        f'{request.scheme}://{request.host}{url_for("role_api")}',
                        headers=header,
                        json={
                            'name': name,
                            'description': description
                        }
                    )
                    if resp.status_code != 201:
                        flash(f'Unable to create role: {resp.json().get("message")}', 'danger')
                    else:
                        flash('Role has been created successfully!', 'success')

            elif action == 'modifyRole':
                name = request.form.get('name')
                description = request.form.get('description')
                if not name:
                    flash('Unable to update Role: Name cannot be emtpy!', 'danger')
                else:
                    if not description:
                        flash('Unable to update Role: Description cannot be emtpy!', 'danger')
                    else:
                        resp = requests.put(
                            f'{request.scheme}://{request.host}{url_for("role_api")}/{name}',
                            headers=header,
                            json={
                                'description': description
                            }
                        )
                        if resp.status_code != 200:
                            flash(f'Unable to update role: {resp.json().get("message")}', 'danger')
                        else:
                            flash('Role has been created successfully!', 'success')

            elif action == 'deleteRole':
                name = request.form.get('name')
                if name:
                    resp = requests.delete(
                        f'{request.scheme}://{request.host}{url_for("role_api")}/{name}',
                        headers=header
                    )
                    if resp.status_code != 200:
                        flash(f'Unable to delete role: {resp.json().get("message")}', 'danger')
                    else:
                        flash('Role has been deleted!', 'success')
                else:
                    flash('You need to provide an name to delete a role!', 'danger')

    role = requests.get(
        f'{request.scheme}://{request.host}{url_for("auth_api")}',
        headers={'Access-Token': session.get('Access-Token')},
    ).json().get('data').get('role').get('name')

    data = dict()
    data['accounts'] = requests.get(
        f'{request.scheme}://{request.host}{url_for("user_api")}',
        headers=header
    ).json().get('data')
    data['roles'] = requests.get(
        f'{request.scheme}://{request.host}{url_for("role_api")}',
        headers=header
    ).json().get('data')
    return render_template('dashboard.html', data=data, role=role), 200
