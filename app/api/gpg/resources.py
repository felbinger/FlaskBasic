from flask.views import MethodView
from flask import request, url_for, current_app, render_template
from marshmallow.exceptions import ValidationError
from flask_mail import Mail
from itsdangerous import (
    URLSafeTimedSerializer, SignatureExpired,
    BadTimeSignature, BadSignature
)

from app.utils import keyserver, gpg, db
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

        if data['fingerprint'] not in [key.keyid for key in keyserver.search(user.email)]:
            return ResultErrorSchema(
                message="Invalid fingerprint!",
                status_code=404
            ).jsonify()

        user.gpg_fingerprint = data['fingerprint']

        db.session.commit()

        # generate token to enable encrypted mails
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        token = s.dumps(user.email, salt='activate-encrypted-mails')

        # send email with verification token to enable account
        mail = Mail(current_app)
        link = f'{request.scheme}://{request.host}{url_for("app.views.default.enable_mail_encryption", token=token)}'
        body = render_template('mail_encrypt_mails.html', link=link)

        fingerprints = list()

        ok = False
        if user.gpg_fingerprint:
            keys = keyserver.search(f'0x{user.gpg_fingerprint}', exact=True)
            if keys and not keys[0].expired:
                # gpg_fingerprint from db is ok
                gpg.import_keys(keys[0].key)
                fingerprints.append(user.gpg_fingerprint)
                ok = True

        if not ok:
            # querying to get keys by email address
            keys = list(filter(lambda k: not k.revoked, keyserver.search(email)))
            for key in keys:
                fingerprints.append(key.keyid)
                gpg.import_keys(key.key)

        body = gpg.encrypt(
            data=body,
            recipients=fingerprints,
            always_trust=True,
            sign=True,
            passphrase=current_app.config.get('PGP_PASSPHRASE')
        ).data.decode().replace("\n", "</br>")

        mail.send_message("Enable encrypted mails!", recipients=[user.email], html=body)

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

        user._gpg_enabled = True
        db.session.commit()

        return ResultSchema(
            data="success",
            status_code=200
        ).jsonify()
