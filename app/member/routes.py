from flask import Blueprint, render_template
from flask_login import login_required, current_user

member = Blueprint('member', __name__, url_prefix='/member')

@member.route('/')
@login_required
def dashboard():
    if current_user.role != 'member':
        return "Unauthorized", 403
    return render_template('member_dashboard.html', user=current_user)
