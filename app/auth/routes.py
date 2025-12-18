from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.extensions import db, login_manager
from datetime import datetime
import cloudinary.uploader
from flask_login import login_user, logout_user
from app.services.auth_services import check_login, get_user_account_by_id, add_user_default

auth = Blueprint('auth', __name__, url_prefix='/auth')

@auth.route('/login', methods=['GET', 'POST'])
def user_login():
    err_msg = None
    if request.method == 'POST':
        username = request.form.get('user_name', '').strip()
        password = request.form.get('password', '').strip()

        # Validate input
        if not username or not password:
            err_msg = "Vui lòng nhập đầy đủ tên người dùng và mật khẩu"
            return render_template('auth/login.html', err_msg=err_msg)

        user_account = check_login(user_name=username, password=password)

        if user_account:
            if user_account.role and user_account.role.name:
                role_name = user_account.role.name.lower()
            elif user_account.member_profile:
                role_name = 'member'
            elif user_account.trainer_profile:
                role_name = 'trainer'
            elif user_account.receptionist_profile:
                role_name = 'receptionist'
            else:
                role_name = None

            if role_name == 'member':
                login_user(user_account)
                return redirect(url_for('member.dashboard'))
            elif role_name == 'trainer':
                login_user(user_account)
                return redirect(url_for('trainer.dashboard'))
            elif role_name == 'admin':
                login_user(user_account)
                return redirect(url_for('admin.index'))
            elif role_name == 'receptionist':
                login_user(user_account)
                return redirect(url_for('receptionist_bp.dashboard'))
            else:
                err_msg = "Tài khoản không có quyền truy cập"
        else:
            err_msg = "Tên người dùng hoặc mật khẩu không chính xác"
    return render_template('auth/login.html',err_msg = err_msg)


@login_manager.user_loader
def user_load(user_id):
    return get_user_account_by_id(user_id)

@auth.route('/logout')
def user_logout():
    logout_user()
    return redirect(url_for('auth.user_login'))

@auth.route('/register',  methods=['GET', 'POST'])
def user_register():
    from app.models import Member, Role
    import hashlib

    err_msg = None

    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        user_name = request.form.get('user_name')
        password = request.form.get('password')
        email = request.form.get('email')
        phone_number = request.form.get('phone_number')
        birth_day = request.form.get('birth_day')
        gender = request.form.get('gender')
        confirm = request.form.get('confirm')

        try:
            # Validate required fields
            if not all([user_name, password, confirm, email]):
                err_msg = "Vui lòng điền đầy đủ thông tin bắt buộc"
                return render_template('auth/register.html', err_msg=err_msg)

            # Validate password match
            if not password.strip() == confirm.strip():
                err_msg = "Mật khẩu không khớp"
                return render_template('auth/register.html', err_msg=err_msg)

            # Check for duplicate username or email
            from app.models import User
            if User.query.filter_by(username=user_name.strip()).first():
                err_msg = "Tên đăng nhập đã tồn tại"
                return render_template('auth/register.html', err_msg=err_msg)
            if User.query.filter_by(email=email.strip()).first():
                err_msg = "Email đã tồn tại"
                return render_template('auth/register.html', err_msg=err_msg)

            # Parse birth_day if provided
            birth_date = None
            if birth_day:
                birth_date = datetime.strptime(birth_day, '%Y-%m-%d').date()

            # Get member role
            role = Role.query.filter_by(name='member').first()
            if not role:
                raise ValueError("Role 'member' không tồn tại trong hệ thống")

            # Hash password
            password_hash = hashlib.md5(password.strip().encode('utf-8')).hexdigest()

            # Create User (without package - will choose package after login)
            user = User(
                username=user_name.strip(),
                email=email.strip(),
                password_hash=password_hash,
                first_name=first_name.strip() if first_name else None,
                last_name=last_name.strip() if last_name else None,
                gender=gender,
                birth_day=birth_date,
                phone=phone_number.strip() if phone_number else None,
                role=role
            )
            db.session.add(user)
            db.session.flush()

            # Create Member profile
            member = Member(user_id=user.id)
            db.session.add(member)

            db.session.commit()

            flash('Đăng ký thành công! Vui lòng đăng nhập và chọn gói tập.', 'success')
            return redirect(url_for('auth.user_login'))

        except ValueError as ve:
            db.session.rollback()
            err_msg = str(ve)
        except Exception as ex:
            db.session.rollback()
            err_msg = f"Lỗi đăng ký: {str(ex)}"

    return render_template('auth/register.html', err_msg=err_msg)