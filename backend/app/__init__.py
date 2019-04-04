import os
from flask import Flask
from flask_cors import CORS

from .api import UserResource, RoleResource, AuthResource, VerificationResource, ResetResource, TwoFAResource
from .db import db
from .config import ProductionConfig, DevelopmentConfig
from .views import default, admin, profile, auth


def create_app(testing_config=None) -> Flask:
    app = Flask(__name__)
    CORS(app)

    # load config
    env = os.environ.get('FLASK_ENV')
    if testing_config is None:
        if env == 'development':
            app.config.from_object(DevelopmentConfig)
        else:
            app.config.from_object(ProductionConfig)
    else:
        app.config.from_object(testing_config)

    # initialize database
    db.init_app(app)
    register_models()

    with app.app_context():
        # create tables
        db.create_all()

    # register resources
    register_resource(app, AuthResource, 'auth_api', '/api/auth', get=False, put=False, delete=False)
    register_resource(app, RoleResource, 'role_api', '/api/roles', pk='name', pk_type='string')
    register_resource(app, UserResource, 'user_api', '/api/users', pk='uuid', pk_type='string')
    register_resource(app, VerificationResource, 'verify_mail_api', '/api/verify', pk='token', pk_type='string',
                      get=False, get_all=False, post=False, delete=False)
    register_resource(app, ResetResource, 'password_reset_api', '/api/reset', pk='token', pk_type='string',
                      get=False, get_all=False, delete=False)
    register_resource(app, TwoFAResource, 'two_factor_api', '/api/2fa', get=False, put=False, delete=False)

    # register views
    app.register_blueprint(default)
    app.register_blueprint(profile)
    app.register_blueprint(admin)
    app.register_blueprint(auth)

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
        app.add_url_rule(f'{url}/<{pk_type}:{pk}>', view_func=view_func, methods=['DELETE'])
