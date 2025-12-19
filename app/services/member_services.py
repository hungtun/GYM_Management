from app.models import User, Member, Membership, GymPackage, Role, Payment
from app.extensions import db
from datetime import datetime, timedelta, timezone
import hashlib

def register_member_with_package(
    first_name, last_name, username, password, email,
    phone_number, gender, birth_day, package_id,
    register_date=None, send_email=True, payment_method=None,
    payment_status="PAID", txn_ref=None
):


    password_hash = hashlib.md5(password.strip().encode("utf-8")).hexdigest()

    # 2. Lấy role member
    role = Role.query.filter_by(name="member").first()
    if not role:
        raise ValueError("Role 'member' không tồn tại trong hệ thống")

    # 3. Kiểm tra username và email đã tồn tại chưa
    if User.query.filter_by(username=username).first():
        raise ValueError("Tên đăng nhập đã tồn tại")
    if User.query.filter_by(email=email).first():
        raise ValueError("Email đã tồn tại")

    # 4. Tạo User
    register_dt = register_date if register_date else datetime.now(timezone.utc)
    user = User(
        username=username.strip(),
        email=email.strip(),
        password_hash=password_hash,
        first_name=first_name.strip() if first_name else None,
        last_name=last_name.strip() if last_name else None,
        gender=gender,
        birth_day=birth_day,
        phone=phone_number.strip() if phone_number else None,
        role=role
    )
    db.session.add(user)
    db.session.flush()

    # 5. Tạo Member
    member = Member(
        user_id=user.id,
        register_date=register_dt
    )
    db.session.add(member)
    db.session.flush()

    # 6. Tạo Membership
    package = GymPackage.query.get(package_id)
    if not package:
        raise ValueError("Gói tập không tồn tại")

    start_date = register_dt
    end_date = start_date + timedelta(days=package.duration_months * 30)


    membership = Membership(
        member_id=member.id,
        package_id=package_id,
        start_date=start_date,
        end_date=end_date,
        active=(payment_status == "PAID")
    )
    db.session.add(membership)
    db.session.flush()

    # 7. Create Payment record
    payment_note = payment_method if payment_method else "Payment for package registration"
    if txn_ref:
        payment_note = "Online payment via Stripe"

    payment = Payment(
        member_id=member.id,
        amount=package.price,
        payment_date=register_dt if payment_status == "PAID" else None,
        note=payment_note,
        status=payment_status,
        txn_ref=txn_ref,
        paid_at=register_dt if payment_status == "PAID" else None
    )
    db.session.add(payment)

    # 8. Commit transaction
    db.session.commit()

    # 9. Send confirmation email (after successful commit, best-effort)
    if send_email and payment_status == "PAID":
        from app.services.email_service import send_registration_confirmation_email
        try:
            send_registration_confirmation_email(user, membership, package)
        except Exception as e:
            print(f"Email error: {str(e)}")

    return user, member, membership, payment

def get_member_list(search=None, status=None):

    from sqlalchemy import or_
    query = Member.query.join(User)

    if search:
        query = query.filter(
            or_(
                User.first_name.like(f'%{search}%'),
                User.last_name.like(f'%{search}%'),
                User.email.like(f'%{search}%'),
                User.phone.like(f'%{search}%')
            )
        )

    if status:
        query = query.filter(Member.status == status)

    return query.order_by(Member.register_date.desc()).all()

def get_member_detail(member_id):

    member = Member.query.get(member_id)
    if not member:
        return None

    # Lấy membership đang hoạt động
    active_membership = Membership.query.filter_by(
        member_id=member_id,
        active=True
    ).first()

    # Lấy tất cả các gói tập (sắp xếp theo ngày bắt đầu mới nhất)
    all_memberships = Membership.query.filter_by(
        member_id=member_id
    ).order_by(Membership.start_date.desc()).all()

    return {
        'member': member,
        'membership': active_membership,
        'all_memberships': all_memberships
    }

def add_package_to_member(member_id, package_id, payment_method="Thanh toán tại quầy"):
    member = Member.query.get(member_id)
    if not member:
        raise ValueError("Hội viên không tồn tại")

    package = GymPackage.query.get(package_id)
    if not package:
        raise ValueError("Gói tập không tồn tại")

    now = datetime.now(timezone.utc)

    # Find the latest membership (by end_date) regardless of active status
    # This ensures we stack packages correctly even if there are pending ones
    latest_membership = Membership.query.filter_by(
        member_id=member_id
    ).order_by(Membership.end_date.desc()).first()

    # Check for currently active membership
    active_membership = Membership.query.filter_by(
        member_id=member_id,
        active=True
    ).first()

    # Calculate start and end dates
    new_membership_active = False

    if latest_membership:
        # Make sure end_date is timezone-aware
        latest_end_date = latest_membership.end_date
        if latest_end_date.tzinfo is None:
            latest_end_date = latest_end_date.replace(tzinfo=timezone.utc)

        if latest_end_date > now:
            # There's a valid package (active or pending): stack new package after it
            start_date = latest_end_date
            end_date = start_date + timedelta(days=package.duration_months * 30)
            new_membership_active = False  # Will be pending until latest package expires
        else:
            # Latest package has expired: activate new package immediately
            # Deactivate old active membership if exists
            if active_membership:
                active_membership.active = False
            start_date = now
            end_date = start_date + timedelta(days=package.duration_months * 30)
            new_membership_active = True
    else:
        # No existing package: activate immediately
        start_date = now
        end_date = start_date + timedelta(days=package.duration_months * 30)
        new_membership_active = True

    # Create new membership
    membership = Membership(
        member_id=member_id,
        package_id=package_id,
        start_date=start_date,
        end_date=end_date,
        active=new_membership_active
    )
    db.session.add(membership)
    db.session.flush()

    # Create payment record (PAID immediately for counter payment)
    payment = Payment(
        member_id=member_id,
        amount=package.price,
        payment_date=now,
        note=f"{payment_method} - {package.name}",
        status="PAID",
        paid_at=now
    )
    db.session.add(payment)

    db.session.commit()

    return membership, payment

def process_payment_callback(txn_ref, status, paid_at=None, raw_response=None):
    """
    Process payment callback from online gateway
    Updates payment status and activates membership if payment successful
    """
    # Find payment by transaction reference
    payment = Payment.query.filter_by(txn_ref=txn_ref).first()
    if not payment:
        raise ValueError(f"Payment with txn_ref {txn_ref} not found")

    # Update payment status
    payment.status = status
    payment.raw_response = raw_response

    if status == "PAID":
        payment.paid_at = paid_at if paid_at else datetime.now(timezone.utc)
        payment.payment_date = payment.paid_at

        # Find and activate membership
        member = payment.member
        membership = Membership.query.filter_by(
            member_id=member.id
        ).order_by(Membership.created_at.desc()).first()

        if membership and not membership.active:
            membership.active = True
            # Update start_date and end_date based on payment time
            package = membership.package
            membership.start_date = payment.paid_at
            membership.end_date = payment.paid_at + timedelta(days=package.duration_months * 30)

        db.session.commit()

        # Gửi email xác nhận đăng ký sau khi thanh toán thành công (online)
        if membership and membership.package and member.user:
            from app.services.email_service import send_registration_confirmation_email
            try:
                send_registration_confirmation_email(member.user, membership, membership.package)
            except Exception as e:
                # Log error but don't rollback if email fails
                print(f"Email error: {str(e)}")

        return payment, membership

    db.session.commit()
    return payment, None

