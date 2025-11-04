from functools import wraps
from flask import abort, redirect, url_for
from flask_login import current_user

def role_required(*roles):
    """
    Decorator để kiểm tra quyền truy cập dựa trên role
    Usage: @role_required('admin', 'receptionist')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.user_login'))
            
            # Get role name from user
            role_name = None
            if current_user.role and current_user.role.name:
                role_name = current_user.role.name.lower()
            elif current_user.member_profile:
                role_name = 'member'
            elif current_user.trainer_profile:
                role_name = 'trainer'
            elif current_user.receptionist_profile:
                role_name = 'receptionist'
            
            # Check if user has required role
            if role_name not in [r.lower() for r in roles]:
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator