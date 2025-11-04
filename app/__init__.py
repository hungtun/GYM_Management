from flask import Flask
from config import Config
from app.extensions import db, migrate, login_manager
from app.models import *


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.user_login'
    login_manager.login_message = 'Vui lòng đăng nhập để tiếp tục'
    login_manager.login_message_category = 'info'
    Config.init_cloudinary()

    from .routes import main
    from .auth.routes import auth
    from .member.routes import member
    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(member)

    return app
