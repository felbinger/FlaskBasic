import os
from pathlib import Path
from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint

from app.api import (
    AuthResource, UserResource, RoleResource,
    RefreshResource, VerificationResource, ResetResource,
    TOTPResource, UploadResource, GPGResource
)
from app.utils import db, gpg, RedisBlacklist
from app.config import ProductionConfig, DevelopmentConfig
from app.views import default, admin, auth


def create_app(testing_config=None) -> Flask:
    app = Flask(__name__)
    CORS(app)

    # load config
    env = os.environ.get('FLASK_ENV')
    if testing_config is None:
        if env == 'development':
            app.config.from_object(DevelopmentConfig)

            # create pgp directories
            Path(app.config['GPG_HOME_DIR']).mkdir(parents=True, exist_ok=True)
            Path(app.config['GPG_SECRET_KEYRING']).mkdir(parents=True, exist_ok=True)
        else:
            app.config.from_object(ProductionConfig)
    else:
        app.config.from_object(testing_config)

    # initialize database
    db.init_app(app)
    register_models()

    # initialize gpg
    gpg.init_app(app)

    # on development setup pgp, in productive done in wsgi_config to prevent gpg init running multiple times (4 workers)
    if not testing_config and env == 'development':
        # check if there keyring contains at least one secret key
        if not len(gpg.list_keys(secret=True)):
            # import keys from keyfile.asc
            if os.path.isfile(f"{app.config['DATA_DIR']}/keyfile.asc"):
                with open(f'{app.config["DATA_DIR"]}/keyfile.asc', 'r') as f:
                    gpg.import_keys(f.read())
            else:
                # generate new key
                data = {
                    'key_type': 'RSA',
                    'key_length': 4096,
                    'name_real': app.config.get('GPG_NAME'),
                    'name_email': app.config.get('GPG_EMAIL'),
                    'passphrase': app.config.get('GPG_PASSPHRASE')
                }
                key = gpg.gen_key(gpg.gen_key_input(**data))

                # export the new generated key pair to keyfile.asc
                with open(f'{app.config["DATA_DIR"]}/keyfile.asc', 'w') as f:
                    f.write(gpg.export_keys(key.fingerprint))
                    f.write(
                        gpg.export_keys(key.fingerprint, secret=True, passphrase=app.config.get('GPG_PASSPHRASE')))

            # check again it the keyring contains at least one secret key
            if not len(gpg.list_keys(secret=True)):
                print("WARNING: pgp functionality is limited")

    # initialize redis blacklist
    if isinstance(app.config.get('BLACKLIST'), RedisBlacklist):
        app.config.get('BLACKLIST').blacklist.init_app(app)

    with app.app_context():
        # create tables
        db.create_all()

    # register resources
    register_resource(app, AuthResource, 'auth_api', '/api/auth', get=False, put=False, delete=False)
    register_resource(app, RefreshResource, 'refresh_api', '/api/auth/refresh', pk='token', pk_type='string',
                      get=False, get_all=False, put=False)
    register_resource(app, RoleResource, 'role_api', '/api/roles', pk='name', pk_type='string')
    register_resource(app, UserResource, 'user_api', '/api/users', pk='uuid', pk_type='string')
    register_resource(app, VerificationResource, 'verify_mail_api', '/api/users/verify', pk='token', pk_type='string',
                      get=False, get_all=False, post=False, delete=False)
    register_resource(app, ResetResource, 'password_reset_api', '/api/reset', pk='token', pk_type='string',
                      get=False, get_all=False, delete=False)
    register_resource(app, TOTPResource, 'two_factor_api', '/api/users/2fa', pk=None, get=False, put=False)
    register_resource(app, UploadResource, 'upload_api', '/api/upload', pk='uuid', pk_type='string',
                      get_all=False, put=False, delete=False)
    register_resource(app, GPGResource, 'gpg_api', '/api/users/gpg', pk='token', pk_type='string',
                      get=False, delete=False)

    # register views
    app.register_blueprint(default)
    app.register_blueprint(admin)
    app.register_blueprint(auth)

    # register swagger ui view
    app.register_blueprint(get_swaggerui_blueprint(
        app.config['SWAGGER_URL'],
        '/swagger.json',
        config={
            'app_name': "Flask Basic"
        }
    ), url_prefix=app.config['SWAGGER_URL'])

    @app.route('/swagger.json')
    def swagger_view():
        return send_from_directory('static/', 'swagger.json')

    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(os.path.join(app.root_path, 'static'),
                                   'favicon.ico', mimetype='image/vnd.microsoft.icon')

    return app


def register_models():
    # noinspection PyUnresolvedReferences
    from .api import User, Role


def register_resource(app, resource, endpoint, url, pk='_id', pk_type='int',
                      get=True, get_all=True, post=True, put=True, delete=True):
    view_func = resource.as_view(endpoint)
    if get_all:
        app.add_url_rule(url, defaults={pk: None} if get else None, view_func=view_func, methods=['GET'])
    if post:
        app.add_url_rule(url, view_func=view_func, methods=['POST'])
    if get:
        app.add_url_rule(f'{url}/<{pk_type}:{pk}>', view_func=view_func, methods=['GET'])
    if put:
        app.add_url_rule(f'{url}/<{pk_type}:{pk}>', view_func=view_func, methods=['PUT'])
    if delete:
        # this solution could be better - think about another way to really have a pk on get/put/delete
        app.add_url_rule(f'{url}/<{pk_type}:{pk}>' if pk else url, view_func=view_func, methods=['DELETE'])
