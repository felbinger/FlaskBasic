from flask import Blueprint, render_template, request, session, url_for, flash, send_from_directory, Markup
# from flask_wtf import FlaskForm
# from wtforms import StringField, PasswordField
# from wtforms.validators import InputRequired, EqualTo
import requests

from .utils import require_login

profile = Blueprint(__name__, 'profile')

"""
class ProfileForm(FlaskForm):
    display_name = StringField('Display Name')
    email = StringField('E-Mail')


class ChangePasswordForm(FlaskForm):
    password = PasswordField('Password')
    password2 = PasswordField('Password (again)', validators=[EqualTo('password')])
"""


@require_login
@profile.route('/profile', methods=['GET', 'POST'])
def account():
    """
    forms = dict()
    forms['modifyProfile'] = ProfileForm
    forms['changePassword'] = ChangePasswordForm
    """
    header = {'Access-Token': session.get('Access-Token')}
    twofa = dict()
    if request.method == 'POST':
        if request.form is not None:
            action = request.form.get('action')

            if action == 'modifyProfile':
                resp = requests.put(
                    f'{request.scheme}://{request.host}{url_for("user_api")}/me',
                    json={
                        '2fa': request.form.get('2faEnabled') == 'on',
                        'displayName': request.form.get('displayName'),
                        'email': request.form.get('email')
                    },
                    headers=header
                )
                if resp.status_code != 200:
                    flash(f'Unable to update account: {resp.json().get("message")}', 'danger')
                else:
                    if '2fa_secret' in resp.json().get('data'):
                        secret = resp.json().get('data').get('2fa_secret')
                        twofa['qr'] = requests.get(
                            f'{request.scheme}://{request.host}{url_for("two_factor_api")}',
                            headers=header
                        ).text
                        twofa['text'] = f'Your new 2FA Secret Key is: <code>{secret}</code>'
                    flash(f'Account has been update!', 'success')

            elif action == 'changePassword':
                public_id = request.form.get('id')
                password = request.form.get('password')
                if public_id:
                    if password == request.form.get('password2'):
                        if len(password) < 8:
                            flash('Password is too short!', 'danger')
                        else:
                            resp = requests.put(
                                f'{request.scheme}://{request.host}{url_for("user_api")}/me',
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

    data = requests.get(
        f'{request.scheme}://{request.host}{url_for("auth_api")}',
        headers=header,
    ).json().get('data')

    if twofa:
        data['2fa'] = twofa

    return render_template('profile.html', data=data, role=role)


# todo redesign
@require_login
@profile.route('/picture/<string:public_id>')
def profile_picture(public_id):
    pic = f'img/profile/{public_id}.png'
    if requests.get(f'{request.scheme}://{request.host}/static/{pic}').status_code != 200:
        pic = f'img/profile/blank.png'
    return send_from_directory('static', pic)
