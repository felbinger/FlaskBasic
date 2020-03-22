from flask.views import MethodView
from flask import request, current_app, url_for, render_template
from itsdangerous import (
    URLSafeTimedSerializer, SignatureExpired,
    BadTimeSignature, BadSignature
)
from typing import Union
from marshmallow.exceptions import ValidationError
from string import digits, ascii_letters
from base64 import b32encode
import os
import random

from app.utils import db, send_mail
from ..schemas import ResultSchema, ResultErrorSchema
from ..authentication import require_token, require_admin
from ..role import Role
from ..user.models import User
from .schemas import (
    DaoCreateUserSchema, DaoUpdateUserSchema,
    DaoRequestPasswordResetSchema
)


def random_string(length=16):
    return ''.join(random.choice(ascii_letters + digits) for i in range(length))


class UserResource(MethodView):
    @require_token
    @require_admin
    def get(self, uuid: str, **_: dict) -> Union[ResultSchema, ResultErrorSchema]:
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
    def post(self, **_: dict) -> Union[ResultSchema, ResultErrorSchema]:
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
        link = f'{request.scheme}://{request.host}{url_for("app.views.auth.verify", token=token)}'
        body = render_template('mail_verify_account.html', link=link, password=data['password'])

        send_mail(subject='Activate your account!', recipient=user, content=body)

        return ResultSchema(
            data=user.jsonify(),
            status_code=201
        ).jsonify()

    @require_token
    def put(self, uuid: str, user: User, **_: dict) -> Union[ResultSchema, ResultErrorSchema]:
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
                            totp_secret = user.totp_secret = b32encode(os.urandom(10)).decode('utf-8')
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
                elif key == 'gpg_enabled':
                    if user.gpg_enabled and not val:
                        user.gpg_enabled = False
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
    def delete(self, uuid: str, **_: dict):
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

    def _update_user_as_admin(self, target: User, **_: dict) -> Union[ResultSchema, ResultErrorSchema]:
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
            elif key == 'gpg_enabled':
                if not val:
                    if target.totp_enabled:
                        target.gpg_enabled = False
                else:
                    if not target.totp_enabled:
                        return ResultErrorSchema(
                            message='You are not allowed to enable GPG.'
                        ).jsonify()
            else:
                setattr(target, key, val)
        db.session.commit()
        data = target.jsonify()
        return ResultSchema(data=data).jsonify()


class VerificationResource(MethodView):
    def put(self, token: str) -> Union[ResultSchema, ResultErrorSchema]:
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
    def post(self) -> Union[ResultSchema, ResultErrorSchema]:
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
            link = f'{request.scheme}://{request.host}{url_for("app.views.auth.confirm_password_reset", token=token)}'
            body = render_template('mail_password_reset.html', link=link, totp=user.totp_enabled)

            send_mail(subject="Password Recovery!", recipient=user, content=body)

        return ResultErrorSchema(
            message='Request has been send. Check your inbox!',
            status_code=200
        ).jsonify()

    def put(self, token: str) -> Union[ResultSchema, ResultErrorSchema]:
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
