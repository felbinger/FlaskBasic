from flask import Blueprint, render_template, request, session, url_for, flash
# from flask_wtf import FlaskForm
# from wtforms import StringField, PasswordField
# from wtforms.validators import InputRequired
import requests

from .utils import require_login

profile = Blueprint(__name__, 'profile')

"""
class ProfileForm(FlaskForm):
    display_name = StringField('Display Name')
    email = StringField('E-Mail')


class ChangePasswordForm(FlaskForm):
    password = PasswordField('Password')
    password2 = PasswordField('Password (again)')
"""


@require_login
@profile.route('/profile/<string:public_id>', methods=['GET', 'POST'])
def account(public_id):
    """
    forms = dict()
    forms['modifyProfile'] = ProfileForm
    forms['changePassword'] = ChangePasswordForm
    """
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
