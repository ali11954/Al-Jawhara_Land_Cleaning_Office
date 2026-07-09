from .auth import auth
from .api import api_bp
from .rest_api import rest_api
from .pages import pages

ALL_BLUEPRINTS = [
    auth,
    api_bp,
    rest_api,
    pages,
]

def register_all_blueprints(app):
    for bp in ALL_BLUEPRINTS:
        app.register_blueprint(bp)