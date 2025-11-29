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

    from .routes import main
    from .auth.routes import auth
    from .member.routes import member
    from .user import user
    from .trainer.routes import trainer
    
    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(member)
    app.register_blueprint(user)
    app.register_blueprint(trainer)

    # Initialize admin after blueprints
    init_admin(app)
    
    # Add redirect for trailing slash
    @app.route('/admin/')
    def admin_redirect():
        from flask import redirect, url_for
        return redirect(url_for('admin.index'))

    return app
