from flask.views import MethodView
from flask import request, current_app, url_for
from flask_mail import Mail
from itsdangerous import (
    URLSafeTimedSerializer, SignatureExpired,
    BadTimeSignature, BadSignature
)
from marshmallow.exceptions import ValidationError
from string import digits, ascii_letters
from io import BytesIO
from base64 import b32encode
import os
import random
import pyqrcode

from app.db import db
from ..schemas import ResultSchema, ResultErrorSchema
from ..authentication import require_token, require_admin
from ..role import Role
from ..user.models import User
from .schemas import (
    DaoCreateUserSchema, DaoUpdateUserSchema,
    DaoRequestPasswordResetSchema, DaoTokenSchema
)


def random_string(length=16):
    return ''.join(random.choice(ascii_letters + digits) for i in range(length))


class UserResource(MethodView):
    @require_token
    @require_admin
    def get(self, uuid, **_):
        if uuid is None:
            return ResultSchema(
                data=[d.jsonify() for d in User.query.all()]
            ).jsonify()
        else:
            data = User.query.filter_by(public_id=uuid).first()
            if not data:
                return ResultErrorSchema(
                    message='User does not exist!',
                    status_code=404
                ).jsonify()
            return ResultSchema(
                data=data.jsonify()
            ).jsonify()

    @require_token
    @require_admin
    def post(self, **_):
        """
        Create an new user account
        """
        schema = DaoCreateUserSchema()
        data = request.get_json() or {}
        try:
            data = schema.load(data)
        except ValidationError as errors:
            return ResultErrorSchema(
                message='Payload is invalid',
                errors=errors.messages,
                status_code=400
            ).jsonify()

        # check if the username is already in use
        user_exists = User.query.filter_by(username=data['username']).first()
        if user_exists:
            return ResultErrorSchema(
                message='Username already in use!',
                status_code=422
            ).jsonify()
        # get the role object
        data['role'] = Role.query.filter_by(name=data.get('role')).first()
        if not data['role']:
            return ResultErrorSchema(
                message='Role does not exist!',
                status_code=404
            ).jsonify()

        # create the user and add it to the database
        user = User(**data)
        db.session.add(user)
        db.session.commit()

        # generate token to verify email
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        token = s.dumps(data['email'], salt='verify-email')

        # send email with verification token to enable account
        mail = Mail(current_app)
        verification_link = f'{request.scheme}://{request.host}{url_for("app.views.auth.verify", token=token)}'
        body = f'Hello, your account has been created. Your password is: <code>{data["password"]}</code>' \
            f'Please click <a href="{verification_link}">here</a> to activate your account.'
        mail.send_message("Activate your account!", recipients=[data['email']], html=body)

        return ResultSchema(
            data=user.jsonify(),
            status_code=201
        ).jsonify()

    @require_token
    def put(self, uuid, user, **_):
        """
        Modify an existing user account
        """
        if uuid == 'me':
            schema = DaoUpdateUserSchema()
            data = request.get_json() or {}
            try:
                data = schema.load(data)
            except ValidationError as errors:
                return ResultErrorSchema(
                    message='Payload is invalid',
                    errors=errors.messages,
                    status_code=400
                ).jsonify()

            if 'role' in data.keys():
                return ResultErrorSchema(
                    message='You are not allowed to change your role!',
                    status_code=403
                ).jsonify()

            totp_secret = None
            totp_deactivation_token = None
            if 'totp_token' in data:
                totp_deactivation_token = data.get('totp_token')
                del data['totp_token']

            for key, val in data.items():
                if key == 'totp_enabled':
                    if val:
                        # generate a new secret
                        if not user.totp_enabled:
                            user.totp_secret = b32encode(os.urandom(10)).decode('utf-8')
                            totp_secret = user.totp_secret
                    else:
                        # deactivate 2fa
                        if user.totp_enabled:
                            # if submitted token is valid
                            if not totp_deactivation_token:
                                return ResultErrorSchema(
                                    message='Unable to deactivate 2fa, token not submitted'
                                ).jsonify()
                            if user.verify_totp(totp_deactivation_token):
                                user.totp_enabled = False
                                user.totp_secret = None
                            else:
                                return ResultErrorSchema(
                                    message='Unable to deactivate 2fa, token is invalid'
                                ).jsonify()
                else:
                    setattr(user, key, val)

            db.session.commit()
            # if a new secret has been created, add it to the data for 2fa activation process
            data = user.jsonify()
            if totp_secret:
                data['2fa_secret'] = totp_secret
            return ResultSchema(data=data).jsonify()
        else:
            target = User.query.filter_by(public_id=uuid).first()
            if not target:
                return ResultErrorSchema(
                    message='User does not exist',
                    status_code=404
                ).jsonify()
            return require_admin(self._update_user_as_admin)(user=user, target=target)

    @require_token
    @require_admin
    def delete(self, uuid, **_):
        """
        Delete an existing account (only with valid public_id not with 'me')
        """
        user = User.query.filter_by(public_id=uuid).first()
        if not user:
            return ResultErrorSchema(
                message='User does not exist',
                status_code=404
            ).jsonify()
        db.session.delete(user)
        db.session.commit()
        return ResultSchema(
            data='Successfully deleted user!',
            status_code=200
        ).jsonify()

    def _update_user_as_admin(self, target, **_):
        schema = DaoUpdateUserSchema()
        data = request.get_json() or {}
        try:
            data = schema.load(data)
        except ValidationError as errors:
            return ResultErrorSchema(
                message='Payload is invalid',
                errors=errors.messages,
                status_code=400
            ).jsonify()

        for key, val in data.items():
            if key == 'role':
                role = Role.query.filter_by(name=val).first()
                if not role:
                    return ResultErrorSchema(
                        message='Invalid Role',
                        status_code=400
                    ).jsonify()
                else:
                    target.role = role
            elif key == 'totp_enabled':
                if not val:
                    if target.totp_enabled:
                        target.totp_enabled = False
                        target.totp_secret = None
                        target.code_viewed = False
                else:
                    if not target.totp_enabled:
                        return ResultErrorSchema(
                            message='You are not allowed to enable 2FA.'
                        ).jsonify()
            else:
                setattr(target, key, val)
        db.session.commit()
        data = target.jsonify()
        return ResultSchema(data=data).jsonify()


class VerificationResource(MethodView):
    def put(self, token):
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            email = s.loads(token, salt='verify-email', max_age=7200)
        except (BadSignature, SignatureExpired, BadTimeSignature):
            return ResultErrorSchema(
                message='Token is invalid!'
            ).jsonify()
        user = User.query.filter_by(email=email).first()
        user.verified = True
        db.session.commit()
        return ResultErrorSchema(
            message='E-Mail verified successfully!',
            status_code=200
        ).jsonify()


class ResetResource(MethodView):
    def post(self):
        """
        Request password reset
        """
        schema = DaoRequestPasswordResetSchema()
        data = request.get_json() or {}
        try:
            data = schema.load(data)
        except ValidationError as errors:
            return ResultErrorSchema(
                message='Payload is invalid',
                errors=errors.messages,
                status_code=400
            ).jsonify()

        # generate token to reset password
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        token = s.dumps(data['email'], salt='reset-password')

        user = User.query.filter_by(email=data['email']).first()
        if user:
            # send email
            mail = Mail(current_app)
            link = f'{request.scheme}://{request.host}{url_for("app.views.auth.confirm_password_reset", token=token)}'
            body = f'Hello, if you want to reset your password, click <a href="{link}">here</a>.\n' + \
                   f'If you haven\'t requested a password reset, just ignore this message.'

            if user.totp_enabled:
                body += f'\nIf you have 2fa enabled and don\'t find your token, you have to contact an Administrator!'

            mail.send_message("Password Recovery", recipients=[data['email']], html=body)

            print(body)

        return ResultErrorSchema(
            message='Request has been send. Check your inbox!',
            status_code=200
        ).jsonify()

    def put(self, token):
        """
        Confirm password reset, by clicking the link in the email (html can't do put so it's the link of the view)
        """
        blacklist = current_app.config.get('BLACKLIST')
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])

        if blacklist.check(token):
            return ResultErrorSchema(
                message='Token is invalid!'
            ).jsonify()

        try:
            email = s.loads(token, salt='reset-password', max_age=7200)
        except (BadSignature, SignatureExpired, BadTimeSignature):
            return ResultErrorSchema(
                message='Token is invalid!'
            ).jsonify()

        blacklist.add(token)

        user = User.query.filter_by(email=email).first()
        if not user:
            return ResultErrorSchema(
                message='User does not exist!'
            ).jsonify()

        # generate new password
        new_password = random_string()

        # update password in database
        user.password = new_password
        db.session.commit()

        return ResultSchema(
            data={'password': new_password},
            status_code=200
        ).jsonify()


class TwoFAResource(MethodView):
    @require_token
    def get(self, user):
        if user.totp_secret and not user.totp_enabled:
            db.session.commit()
            url = pyqrcode.create(user.get_totp_uri())
            stream = BytesIO()
            url.svg(stream, scale=current_app.config['QR_SCALE'])
            return stream.getvalue(), 200, {
                'Content-Type': 'image/svg+xml',
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
            }
        return ResultErrorSchema(message='Unable to generate QR Code').jsonify()

    @require_token
    def post(self, user):
        """
        Activate 2FA with a valid token
        """
        schema = DaoTokenSchema()
        data = request.get_json() or {}
        try:
            data = schema.load(data)
        except ValidationError as errors:
            return ResultErrorSchema(
                message='Payload is invalid',
                errors=errors.messages,
                status_code=400
            ).jsonify()

        if not user.totp_secret:
            return ResultErrorSchema(
                message='2fa is not setted up',
                status_code=400
            ).jsonify()
        if user.verify_totp(data['token']):
            user.totp_enabled = True
            db.session.commit()
            return ResultErrorSchema(
                message='2fa has been enabled',
                status_code=200
            ).jsonify()
        else:
            return ResultErrorSchema(
                message='invalid token, try again',
                status_code=400
            ).jsonify()

    @require_token
    def delete(self, user):
        """
        reset 2fa secret key if it's not enabled, just prepared for setup
        """
        if user.totp_enabled and user.totp_secret:
            return ResultErrorSchema(
                message='2fa is not in setup state, this can\'t be aborted!'
            ).jsonify()

        user.totp_secret = None
        db.session.commit()
        return ResultSchema(
            data='2fa secret has been disabled'
        ).jsonify()
