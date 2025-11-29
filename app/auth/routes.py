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
                return redirect(url_for('main.index'))
            elif role_name == 'trainer':
                login_user(user_account)
                return redirect(url_for('trainer.dashboard'))  
            elif role_name == 'admin':
                login_user(user_account)
                return redirect(url_for('admin.index'))
            elif role_name == 'receptionist':
                login_user(user_account)
                return redirect('/receptionist')  
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
            if password.strip().__eq__(confirm.strip()):
                add_user_default(first_name=first_name,
                        last_name=last_name,
                        user_name= user_name,
                        password= password,
                        email=email,
                        phone_number=phone_number,
                        gender=gender,
                        birth_day=datetime.strptime(birth_day, '%Y-%m-%d').date(),
                        )
                return redirect(url_for('auth.user_login'))
            else:
                err_msg = "Mật khẩu không khớp"
                return redirect(url_for('auth.user_login'))
        except Exception as ex :
            db.session.rollback() 
            err_msg = "Could not add user" + str(ex)
        
    return render_template('auth/register.html', err_msg = err_msg)