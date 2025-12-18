from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import GymPackage, Member, Membership, Payment
from app.extensions import db
from datetime import datetime, timedelta, timezone

member = Blueprint('member', __name__, url_prefix='/member')

@member.route('/')
@login_required
def dashboard():
    """Member dashboard - hiển thị thông tin hội viên và gói tập hiện tại"""
    member = Member.query.filter_by(user_id=current_user.id).first()

    # Lấy membership đang active
    active_membership = None
    if member:
        active_membership = Membership.query.filter_by(
            member_id=member.id,
            active=True
        ).first()

    return render_template('member/dashboard.html',
                         user=current_user,
                         member=member,
                         active_membership=active_membership)

@member.route('/packages')
@login_required
def view_packages():
    """Trang xem và chọn các gói tập"""
    packages = GymPackage.query.all()
    member = Member.query.filter_by(user_id=current_user.id).first()

    # Kiểm tra xem member đã có gói chưa
    has_active_package = False
    if member:
        active_membership = Membership.query.filter_by(
            member_id=member.id,
            active=True
        ).first()
        has_active_package = active_membership is not None

    return render_template('member/packages.html',
                         packages=packages,
                         has_active_package=has_active_package)

@member.route('/select-package/<int:package_id>', methods=['POST'])
@login_required
def select_package(package_id):
    """Xử lý khi member chọn gói - tạo Payment PENDING và redirect sang thanh toán"""
    try:
        member = Member.query.filter_by(user_id=current_user.id).first()
        if not member:
            flash('Không tìm thấy thông tin hội viên', 'error')
            return redirect(url_for('member_bp.view_packages'))

        package = GymPackage.query.get(package_id)
        if not package:
            flash('Gói tập không tồn tại', 'error')
            return redirect(url_for('member_bp.view_packages'))

        # Tạo Membership (chưa active)
        start_date = datetime.now(timezone.utc)
        end_date = start_date + timedelta(days=package.duration_months * 30)

        membership = Membership(
            member_id=member.id,
            package_id=package_id,
            start_date=start_date,
            end_date=end_date,
            active=False  # Chưa active, chờ thanh toán
        )
        db.session.add(membership)
        db.session.flush()

        # Tạo Payment PENDING
        import uuid
        txn_ref = f"GYM_{member.id}_{int(datetime.now().timestamp())}"

        payment = Payment(
            member_id=member.id,
            amount=package.price,
            payment_date=None,
            note=f"Đăng ký gói {package.name} - Chờ thanh toán online",
            status="PENDING",
            txn_ref=txn_ref
        )
        db.session.add(payment)
        db.session.commit()

        # TODO: Tích hợp Stripe - tạo checkout session
        # Hiện tại redirect về trang thông báo
        flash(f'Đã chọn gói {package.name}. Vui lòng thanh toán để kích hoạt.', 'info')

        # TODO: Thay bằng redirect sang Stripe Checkout
        # return redirect(stripe_checkout_url)

        # Tạm thời redirect về packages với thông báo
        return redirect(url_for('member_bp.view_packages'))

    except Exception as e:
        db.session.rollback()
        flash(f'Lỗi: {str(e)}', 'error')
        return redirect(url_for('member_bp.view_packages'))
