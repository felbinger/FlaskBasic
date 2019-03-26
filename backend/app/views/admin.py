from flask import Blueprint, render_template, request, session, url_for, flash
# from flask_wtf import FlaskForm
# from wtforms import StringField, PasswordField, SelectField, HiddenField
import requests

from .utils import require_login, require_admin

admin = Blueprint(__name__, 'admin')

"""
class CreateAccountForm(FlaskForm):
    username = StringField('username')
    email = StringField('email')
    password = PasswordField('password')
    role = SelectField('role')


class ModifyAccountForm(FlaskForm):
    public_id = HiddenField('id')
    username = StringField('username')
    email = StringField('email')
    display_name = StringField('displayName')
    role = SelectField('role')


class ChangePasswordForm(FlaskForm):
    public_id = HiddenField('id')
    password = PasswordField('password')
    password2 = PasswordField('password2')


class DeleteAccountForm(FlaskForm):
    public_id = HiddenField('id')


class CreateRoleForm(FlaskForm):
    name = StringField('name')
    description = StringField('description')


class ModifyRoleForm(FlaskForm):
    name = StringField('name')
    description = StringField('description')


class DeleteRoleForm(FlaskForm):
    name = StringField('name')
"""


@require_login
@require_admin
@admin.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    """
    forms = dict()
    forms['createAccount'] = CreateAccountForm
    forms['modifyAccount'] = ModifyAccountForm
    forms['changePassword'] = ChangePasswordForm
    forms['deleteAccount'] = DeleteAccountForm
    forms['createRole'] = CreateRoleForm
    forms['modifyRole'] = ModifyRoleForm
    forms['deleteRole'] = DeleteRoleForm
    """
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
