import stripe
from flask import url_for
from app.extensions import db
from app.models import Payment, Membership, Member, GymPackage, PTPackage, PTSubscription
import logging

stripe_logger = logging.getLogger('stripe_service')
stripe_logger.setLevel(logging.INFO)


def init_stripe(app):
    """Initialize Stripe with API key"""
    stripe.api_key = app.config.get('STRIPE_SECRET_KEY')
    stripe_logger.info("Stripe service initialized")


def create_checkout_session(member, package, success_url, cancel_url, package_type='GYM'):
    """
    Create a Stripe Checkout Session for package payment

    Args:
        member: Member object
        package: GymPackage or PTPackage object
        success_url: URL to redirect after successful payment
        cancel_url: URL to redirect if payment is cancelled
        package_type: 'GYM' or 'PT'

    Returns:
        Checkout Session object with session.url for redirect
    """
    try:
        # Create line items for Stripe
        line_items = [{
            'price_data': {
                'currency': 'vnd',
                'product_data': {
                    'name': package.name,
                    'description': f'Gói tập {package.duration_months} tháng tại GYM Beta',
                },
                'unit_amount': int(package.price),  # Stripe expects amount in smallest currency unit
            },
            'quantity': 1,
        }]

        # Create checkout session
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            client_reference_id=f"{member.id}_{package.id}",
            customer_email=member.user.email,
            metadata={
                'member_id': member.id,
                'package_id': package.id,
                'package_name': package.name,
                'package_type': package_type,  # Thêm package_type vào metadata
            }
        )

        stripe_logger.info(f"Created Stripe checkout session: {session.id} for member {member.id}")
        return session

    except stripe.error.StripeError as e:
        stripe_logger.error(f"Stripe error: {str(e)}")
        raise Exception(f"Không thể tạo phiên thanh toán: {str(e)}")
    except Exception as e:
        stripe_logger.error(f"Error creating checkout session: {str(e)}")
        raise


def handle_checkout_session_completed(session):
    """
    Handle successful payment from Stripe webhook

    Args:
        session: Stripe checkout.session.completed event data (can be dict or Stripe object)
    """
    try:
        # Handle both dict and Stripe object
        if isinstance(session, dict):
            metadata = session.get('metadata', {})
            session_id = session.get('id', '')
        else:
            # Stripe object
            metadata = session.metadata if hasattr(session, 'metadata') and session.metadata else {}
            session_id = session.id if hasattr(session, 'id') else ''
        
        member_id = int(metadata.get('member_id'))
        package_id = int(metadata.get('package_id'))
        package_type = metadata.get('package_type', 'GYM')  # Default to GYM

        # Get member
        member = Member.query.get(member_id)
        if not member:
            stripe_logger.error(f"Member {member_id} not found")
            return

        from datetime import datetime, timedelta, timezone
        now = datetime.now(timezone.utc)

        if package_type == 'PT':
            # Xử lý PT Package - tạo PTSubscription
            pt_package = PTPackage.query.get(package_id)
            if not pt_package:
                stripe_logger.error(f"PTPackage {package_id} not found")
                return

            # Tạo PTSubscription
            # start_date và end_date sẽ được set khi trainer accept subscription
            # Không cần tính toán start_date/end_date ở đây vì sẽ được set khi trainer nhận
            pt_subscription = PTSubscription(
                member_id=member_id,
                pt_package_id=package_id,
                trainer_id=None,  # Chưa có trainer nhận
                start_date=None,  # Sẽ được set khi trainer accept
                end_date=None,  # Sẽ được tính lại khi trainer accept (dựa trên start_date + duration)
                active=False,  # Chưa active vì chưa có trainer
                status='pending'  # Chờ trainer nhận
            )
            db.session.add(pt_subscription)

            # Tạo payment record
            payment = Payment(
                member_id=member_id,
                amount=pt_package.price,
                payment_date=datetime.now(timezone.utc),
                note=f"Thanh toán gói PT {pt_package.name} qua Stripe",
                status="PAID",
                txn_ref=session_id,
                paid_at=datetime.now(timezone.utc),
                raw_response=str(session)
            )
            db.session.add(payment)

            stripe_logger.info(f"Successfully created PTSubscription for member {member_id}, session {session_id}")

        else:
            # Xử lý GYM Package - tạo Membership
            gym_package = GymPackage.query.get(package_id)
            if not gym_package:
                stripe_logger.error(f"GymPackage {package_id} not found")
                return

            # Tìm latest membership của member này
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
                latest_end_date = latest_membership.end_date
                if latest_end_date and latest_end_date.tzinfo is None:
                    latest_end_date = latest_end_date.replace(tzinfo=timezone.utc)

                if latest_end_date and latest_end_date > now:
                    # Có membership còn hiệu lực: stack sau đó
                    start_date = latest_end_date
                    end_date = start_date + timedelta(days=gym_package.duration_months * 30)
                    new_membership_active = False
                    stripe_logger.info(f"Creating pending membership for member {member_id}. Starts: {start_date}, Ends: {end_date}")
                else:
                    # Membership đã hết hạn: activate ngay
                    if active_membership:
                        active_membership.active = False
                    start_date = now
                    end_date = start_date + timedelta(days=gym_package.duration_months * 30)
                    new_membership_active = True
                    stripe_logger.info(f"Old package expired. Activating new membership immediately for member {member_id}")
            else:
                # Chưa có membership: activate ngay
                start_date = now
                end_date = start_date + timedelta(days=gym_package.duration_months * 30)
                new_membership_active = True

            membership = Membership(
                member_id=member_id,
                package_id=package_id,
                start_date=start_date,
                end_date=end_date,
                active=new_membership_active
            )
            db.session.add(membership)

            # Create payment record
            payment = Payment(
                member_id=member_id,
                amount=gym_package.price,
                payment_date=datetime.now(timezone.utc),
                note=f"Thanh toán gói {gym_package.name} qua Stripe",
                status="PAID",
                txn_ref=session_id,
                paid_at=datetime.now(timezone.utc),
                raw_response=str(session)
            )
            db.session.add(payment)

            stripe_logger.info(f"Successfully processed payment for member {member_id}, session {session_id}")

            # Send confirmation email
            try:
                from app.services.email_service import send_registration_confirmation_email
                send_registration_confirmation_email(member.user, membership, gym_package)
            except Exception as email_error:
                stripe_logger.warning(f"Could not send email: {str(email_error)}")

        db.session.commit()

    except Exception as e:
        db.session.rollback()
        stripe_logger.error(f"Error handling checkout session: {str(e)}")
        raise

