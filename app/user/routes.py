from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from cloudinary.uploader import upload as cloudinary_upload

from app.services.user_services import get_user_profile_context, update_user_profile

user = Blueprint('user', __name__, url_prefix='/user')


@user.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        profile_data = request.form.to_dict()
        avatar_file = request.files.get('avatar')
        if avatar_file and avatar_file.filename:
            try:
                result = cloudinary_upload(
                    avatar_file,
                    folder="gym_management/avatars",
                    public_id=f"user_{current_user.id}",
                    overwrite=True,
                    resource_type="image"
                )
                profile_data['avatar_url'] = result.get('secure_url')
            except Exception as exc:
                flash(f'Không thể tải ảnh đại diện: {exc}', 'error')
        update_user_profile(current_user, profile_data)
        flash('Cập nhật hồ sơ thành công', 'success')
        return redirect(url_for('user.profile'))

    context = get_user_profile_context(current_user)
    return render_template(
        'user/profile.html',
        user=current_user,
        role=context.get('role'),
        extra=context.get('extra'),
        stats=context.get('stats')
    )

