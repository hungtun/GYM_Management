from flask import Flask
from config import Config
from app.extensions import db, migrate, login_manager
from app.models import *
from .admin import init_admin



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

    # Initialize email service
    from app.services.email_service import init_email
    init_email(app)

    from .routes import main
    from .auth.routes import auth
    from .member.routes import member
    from .receptionist.routes import receptionist

    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(member)
    app.register_blueprint(receptionist)

    # Initialize admin after blueprints
    init_admin(app)

    # Add redirect for trailing slash
    @app.route('/admin/')
    def admin_redirect():
        from flask import redirect, url_for
        return redirect(url_for('admin.index'))

    # Add datetime to Jinja context
    @app.context_processor
    def inject_now():
        from datetime import datetime
        return {'now': datetime.now}

    return app
