from flask.views import MethodView
from flask import request, url_for, current_app, render_template
from marshmallow.exceptions import ValidationError
from itsdangerous import (
    URLSafeTimedSerializer, SignatureExpired,
    BadTimeSignature, BadSignature
)

from app.utils import keyserver, send_mail, db
from ..schemas import ResultSchema, ResultErrorSchema
from ..authentication import require_token
from ..user import User
from .schemas import DaoFingerprintSchema


class GPGResource(MethodView):
    @require_token
    def get(self, user):
        # get keys for the email address of the user
        keys = keyserver.search(user.email)
        # remove expired keys
        if keys:
            keys = list(filter(lambda key: not key.expired, keys))
        if not keys:
            return ResultErrorSchema(
                message='Unable to find PGP keys for this email address!',
                status_code=404
            ).jsonify()
        return ResultSchema(
            data=[key.keyid for key in keys]
        ).jsonify()

    @require_token
    def post(self, user):
        """
        send encrypted email to confirm your request to only send encrypted messages in the future
        """
        schema = DaoFingerprintSchema()
        data = request.get_json() or {}
        try:
            data = schema.load(data)
        except ValidationError as errors:
            return ResultErrorSchema(
                message='Payload is invalid',
                errors=errors.messages
            ).jsonify()

        keys = list(filter(lambda k: not k.expired and k.keyid == data['fingerprint'], keyserver.search(user.email)))
        if not keys:
            return ResultErrorSchema(
                message="Invalid fingerprint!",
                status_code=404
            ).jsonify()

        key = keys.pop()

        user.gpg_fingerprint = key.keyid
        user.gpg_public_key = key.key.encode()

        db.session.commit()

        # generate token to enable encrypted mails
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        token = s.dumps(user.email, salt='activate-encrypted-mails')

        # send email with verification token to enable account
        link = f'{request.scheme}://{request.host}{url_for("app.views.default.enable_mail_encryption", token=token)}'
        body = render_template('mail_encrypt_mails.html', link=link)

        send_mail(subject="Enable encrypted mails!", recipient=user, content=body, force_gpg=True)

        return ResultSchema(
            data='a confirmation email has been send, please decrypt it and click on the link to confirm ',
            status_code=201
        ).jsonify()

    def put(self, token):
        """
        resource to confirm that emails should be encrypted in the future
        (will be accessed if the link in the email is clicked)
        """
        blacklist = current_app.config.get('BLACKLIST')
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])

        if blacklist.check(token):
            return ResultErrorSchema(
                message='Token is invalid!'
            ).jsonify()

        try:
            email = s.loads(token, salt='activate-encrypted-mails', max_age=7200)
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

        user.gpg_enabled = True
        db.session.commit()

        return ResultSchema(
            data="success",
            status_code=200
        ).jsonify()
