from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import GymPackage, Member, Membership, Payment
from app.extensions import db
from datetime import datetime, timedelta, timezone
import stripe

member = Blueprint('member', __name__, url_prefix='/member')

@member.route('/')
@login_required
def dashboard():
    """Member dashboard - hiển thị thông tin hội viên và gói tập hiện tại"""
    member = Member.query.filter_by(user_id=current_user.id).first()

    # Auto-activate pending memberships if current one expired
    if member:
        _check_and_activate_pending_memberships(member.id)

    # Lấy membership đang active
    active_membership = None
    all_memberships = []
    if member:
        active_membership = Membership.query.filter_by(
            member_id=member.id,
            active=True
        ).first()

        # Lấy tất cả các gói tập đã mua (sắp xếp theo ngày bắt đầu mới nhất)
        all_memberships = Membership.query.filter_by(
            member_id=member.id
        ).order_by(Membership.start_date.desc()).all()

    return render_template('member/dashboard.html',
                         user=current_user,
                         member=member,
                         active_membership=active_membership,
                         all_memberships=all_memberships)


def _check_and_activate_pending_memberships(member_id):
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)

    # Process GYM packages
    _activate_pending_for_package_type(member_id, 'GYM', now)

    # Process PT packages
    _activate_pending_for_package_type(member_id, 'PT', now)


def _activate_pending_for_package_type(member_id, package_type, now):
    """Activate pending membership for a specific package type"""

    # Get current active membership of this type
    active_membership = Membership.query.join(
        GymPackage, Membership.package_id == GymPackage.id
    ).filter(
        Membership.member_id == member_id,
        Membership.active == True,
        GymPackage.package_type == package_type
    ).first()

    # If active membership expired, deactivate it
    if active_membership and active_membership.end_date:
        end_date_aware = active_membership.end_date
        if end_date_aware.tzinfo is None:
            end_date_aware = end_date_aware.replace(tzinfo=timezone.utc)

        if end_date_aware <= now:
            # Deactivate expired membership
            active_membership.active = False

            # Find next pending membership of the same type (earliest start date)
            next_membership = Membership.query.join(
                GymPackage, Membership.package_id == GymPackage.id
            ).filter(
                Membership.member_id == member_id,
                Membership.active == False,
                GymPackage.package_type == package_type,
                Membership.start_date <= now
            ).order_by(Membership.start_date.asc()).first()

            if next_membership:
                next_membership.active = True
                db.session.commit()

@member.route('/packages')
@login_required
def view_packages():
    """Trang xem và chọn các gói tập"""
    packages = GymPackage.query.filter_by(package_type='GYM').all()
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


@member.route('/pt-packages')
@login_required
def view_pt_packages():
    """Trang xem và chọn các gói PT (Personal Trainer)"""
    packages = GymPackage.query.filter_by(package_type='PT').all()
    member = Member.query.filter_by(user_id=current_user.id).first()

    # Check if member has ACTIVE GYM package (required to purchase PT)
    has_gym_package = False
    if member:
        now = datetime.now(timezone.utc)

        # Find GYM packages that are active OR still valid
        gym_memberships = Membership.query.join(
            GymPackage, Membership.package_id == GymPackage.id
        ).filter(
            Membership.member_id == member.id,
            GymPackage.package_type == 'GYM'
        ).all()

        # Check if any GYM membership is still valid
        for membership in gym_memberships:
            end_date = membership.end_date
            if end_date and end_date.tzinfo is None:
                end_date = end_date.replace(tzinfo=timezone.utc)

            if membership.active or (end_date and end_date > now):
                has_gym_package = True
                break

    # Kiểm tra xem member đã có gói PT chưa
    has_active_package = False
    if member:
        active_membership = Membership.query.filter_by(
            member_id=member.id,
            active=True
        ).first()
        has_active_package = active_membership is not None

    return render_template('member/pt_packages.html',
                         packages=packages,
                         has_active_package=has_active_package,
                         has_gym_package=has_gym_package)

@member.route('/create-checkout-session/<int:package_id>', methods=['POST'])
@login_required
def create_checkout_session(package_id):
    """Create Stripe Checkout Session and redirect to payment page"""
    try:
        member_obj = Member.query.filter_by(user_id=current_user.id).first()
        if not member_obj:
            flash('Không tìm thấy thông tin hội viên', 'error')
            return redirect(url_for('member.view_packages'))

        package = GymPackage.query.get(package_id)
        if not package:
            flash('Gói tập không tồn tại', 'error')
            return redirect(url_for('member.view_packages'))

        # If trying to buy PT package, check if member has ACTIVE GYM package first
        if package.package_type == 'PT':
            now = datetime.now(timezone.utc)

            # Find GYM packages that are active OR still valid
            gym_memberships = Membership.query.join(
                GymPackage, Membership.package_id == GymPackage.id
            ).filter(
                Membership.member_id == member_obj.id,
                GymPackage.package_type == 'GYM'
            ).all()

            # Check if any GYM membership is still valid
            has_valid_gym = False
            for membership in gym_memberships:
                end_date = membership.end_date
                if end_date and end_date.tzinfo is None:
                    end_date = end_date.replace(tzinfo=timezone.utc)

                if membership.active or (end_date and end_date > now):
                    has_valid_gym = True
                    break

            if not has_valid_gym:
                flash('Bạn cần có gói tập GYM đang hoạt động để đăng ký gói PT!', 'error')
                return redirect(url_for('member.view_packages'))

        # Import Stripe service
        from app.services.stripe_service import create_checkout_session as create_stripe_session

        # Create success and cancel URLs
        success_url = url_for('member.payment_success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}'
        cancel_url = url_for('member.payment_cancel', _external=True)

        # Create Stripe checkout session
        session = create_stripe_session(
            member=member_obj,
            package=package,
            success_url=success_url,
            cancel_url=cancel_url
        )

        # Redirect to Stripe Checkout
        return redirect(session.url, code=303)

    except Exception as e:
        flash(f'Lỗi tạo phiên thanh toán: {str(e)}', 'error')
        return redirect(url_for('member.view_packages'))


@member.route('/payment/success')
@login_required
def payment_success():
    """Handle successful payment redirect from Stripe"""
    session_id = request.args.get('session_id')

    if session_id:
        flash('Thanh toán thành công! Gói tập của bạn đã được kích hoạt.', 'success')
    else:
        flash('Thanh toán đang được xử lý.', 'info')

    return redirect(url_for('member.dashboard'))


@member.route('/payment/cancel')
@login_required
def payment_cancel():
    """Handle cancelled payment from Stripe"""
    flash('Thanh toán đã bị hủy. Vui lòng thử lại.', 'warning')
    return redirect(url_for('member.view_packages'))


@member.route('/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events"""
    import json
    import logging

    webhook_logger = logging.getLogger('stripe_webhook')

    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')

    from flask import current_app
    webhook_secret = current_app.config.get('STRIPE_WEBHOOK_SECRET')

    # Test mode: bypass signature verification if webhook_secret is default or not set
    if not webhook_secret or webhook_secret == 'whsec_...':
        # Test mode - parse JSON directly without verification
        webhook_logger.warning("⚠️ TEST MODE: Webhook signature verification is DISABLED. Do NOT use in production!")
        try:
            event = json.loads(payload)
        except json.JSONDecodeError:
            return jsonify({'error': 'Invalid JSON payload'}), 400
    else:
        # Production mode - verify signature
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
        except ValueError:
            return jsonify({'error': 'Invalid payload'}), 400
        except stripe.error.SignatureVerificationError:
            return jsonify({'error': 'Invalid signature'}), 400

    # Handle checkout.session.completed event
    if event.get('type') == 'checkout.session.completed':
        session = event.get('data', {}).get('object')

        if not session:
            return jsonify({'error': 'Invalid session data'}), 400

        # Process the payment
        from app.services.stripe_service import handle_checkout_session_completed
        try:
            handle_checkout_session_completed(session)
        except Exception as e:
            webhook_logger.error(f"Error processing payment: {str(e)}")
            return jsonify({'error': str(e)}), 500

    return jsonify({'success': True}), 200
