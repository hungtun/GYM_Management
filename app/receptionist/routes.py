from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.decorators import role_required
from app.models import GymPackage, Member, User, Membership, Payment
from app.extensions import db
from app.services.member_services import (
    register_member_with_package,
    get_member_list,
    get_member_detail,
    add_package_to_member
)
from app.services.email_service import send_registration_confirmation_email
from datetime import datetime

receptionist = Blueprint('receptionist_bp', __name__, url_prefix='/receptionist')

@receptionist.route('/dashboard')
@login_required
@role_required('receptionist', 'admin')
def dashboard():
    members = get_member_list()
    packages = GymPackage.query.all()
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('receptionist/dashboard.html',
                         members=members,
                         packages=packages,
                         today=today)

@receptionist.route('/register-member', methods=['GET', 'POST'])
@login_required
@role_required('receptionist', 'admin')
def register_member():
    packages = GymPackage.query.all()

    if request.method == 'POST':
        try:
            first_name = request.form.get('first_name', '').strip()
            last_name = request.form.get('last_name', '').strip()
            username = request.form.get('user_name', '').strip()
            password = request.form.get('password', '').strip()
            email = request.form.get('email', '').strip()
            phone_number = request.form.get('phone_number', '').strip()
            birth_day = request.form.get('birth_day')
            gender = request.form.get('gender')
            package_id = request.form.get('package_id')
            register_date = request.form.get('register_date')
            payment_method = request.form.get('payment_method', 'Cash')  # Cash/Transfer/POS

            # Validate required fields (based on model constraints)
            if not all([username, password, email, package_id]):
                flash("Vui lòng điền đầy đủ thông tin bắt buộc (tên đăng nhập, mật khẩu, email, gói tập)", 'error')
            else:
                # Parse dates
                birth_date = datetime.strptime(birth_day, '%Y-%m-%d').date() if birth_day else None
                reg_date = datetime.strptime(register_date, '%Y-%m-%d') if register_date else datetime.utcnow()

                # Register member at counter with PAID status (customer paid at counter)
                user, member, membership, payment = register_member_with_package(
                    first_name=first_name,
                    last_name=last_name,
                    username=username,
                    password=password,
                    email=email,
                    phone_number=phone_number,
                    gender=gender,
                    birth_day=birth_date,
                    package_id=int(package_id),
                    register_date=reg_date,
                    payment_status="PAID",  # Counter registration = PAID immediately
                    payment_method="Thanh toán tại quầy",
                    send_email=True  # Send confirmation email after successful registration
                )

                flash(f"Đăng ký thành công! Hội viên: {user.first_name} {user.last_name}", 'success')
                return redirect(url_for('receptionist_bp.dashboard'))

        except ValueError as ve:
            db.session.rollback()
            flash(str(ve), 'error')
        except Exception as e:
            db.session.rollback()
            flash(f"Lỗi đăng ký: {str(e)}", 'error')

    today = datetime.now().strftime('%Y-%m-%d')
    members = get_member_list()
    return render_template('receptionist/dashboard.html',
                         packages=packages,
                         members=members,
                         today=today)

@receptionist.route('/member/<int:member_id>/detail')
@login_required
@role_required('receptionist', 'admin')
def member_detail(member_id):
    """Lấy chi tiết hội viên (AJAX)"""
    from datetime import datetime, timezone

    member_data = get_member_detail(member_id)
    if not member_data:
        return jsonify({'error': 'Không tìm thấy hội viên'}), 404

    # Check if member has active GYM package (for PT validation)
    now = datetime.now(timezone.utc)
    has_valid_gym = False

    gym_memberships = Membership.query.join(
        GymPackage, Membership.package_id == GymPackage.id
    ).filter(
        Membership.member_id == member_id,
        GymPackage.package_type == 'GYM'
    ).all()

    for membership in gym_memberships:
        end_date = membership.end_date
        if end_date and end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)

        if membership.active or (end_date and end_date > now):
            has_valid_gym = True
            break

    # Render HTML cho modal từ template partials
    info_html = render_template(
        'receptionist/partials/member_info.html',
        member=member_data['member']
    )

    membership_html = render_template(
        'receptionist/partials/membership_info.html',
        membership=member_data['membership'],
        all_memberships=member_data.get('all_memberships', [])
    )

    return jsonify({
        'info_html': info_html,
        'membership_html': membership_html,
        'member_id': member_id,
        'has_valid_gym': has_valid_gym
    })

@receptionist.route('/member/<int:member_id>/add-package', methods=['POST'])
@login_required
@role_required('receptionist', 'admin')
def add_package(member_id):
    """Thêm gói tập cho hội viên"""
    try:
        package_id = request.form.get('package_id')
        payment_method = request.form.get('payment_method', 'Thanh toán tại quầy')

        if not package_id:
            flash('Vui lòng chọn gói tập', 'error')
            return redirect(url_for('receptionist_bp.dashboard'))

        membership, payment = add_package_to_member(
            member_id,
            int(package_id),
            payment_method=payment_method
        )

        # Display appropriate message based on membership status
        if membership.active:
            flash(f'Đăng ký gói thành công! Gói đã được kích hoạt.', 'success')
        else:
            flash(f'Đăng ký gói thành công! Gói sẽ tự động kích hoạt khi gói hiện tại hết hạn.', 'success')

        # Gửi email thông báo
        member = Member.query.get(member_id)
        if member and member.user:
            send_registration_confirmation_email(
                member.user,
                membership,
                membership.package
            )

    except Exception as e:
        db.session.rollback()
        flash(f'Lỗi: {str(e)}', 'error')

    return redirect(url_for('receptionist_bp.dashboard'))

