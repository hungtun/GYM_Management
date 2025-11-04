from functools import wraps
from flask import abort, redirect,url_for
from flask_login import current_user

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.user.role not in roles:
                abort(403)  
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def role_redirect():

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.is_authenticated:
                user_role = current_user.user.role
                if user_role == 'doctor':
                    return redirect(url_for('doctor_user.doctor_detail'))
                elif user_role == 'patient':
                    return redirect(url_for('auth.user_page'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator