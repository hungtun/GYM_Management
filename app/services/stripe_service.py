import stripe
from flask import url_for
from app.extensions import db
from app.models import Payment, Membership, Member, GymPackage
import logging

stripe_logger = logging.getLogger('stripe_service')
stripe_logger.setLevel(logging.INFO)


def init_stripe(app):
    """Initialize Stripe with API key"""
    stripe.api_key = app.config.get('STRIPE_SECRET_KEY')
    stripe_logger.info("Stripe service initialized")


def create_checkout_session(member, package, success_url, cancel_url):
    """
    Create a Stripe Checkout Session for package payment

    Args:
        member: Member object
        package: GymPackage object
        success_url: URL to redirect after successful payment
        cancel_url: URL to redirect if payment is cancelled

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
        session: Stripe checkout.session.completed event data
    """
    try:
        member_id = int(session.metadata.get('member_id'))
        package_id = int(session.metadata.get('package_id'))

        # Get member and package
        member = Member.query.get(member_id)
        package = GymPackage.query.get(package_id)

        if not member or not package:
            stripe_logger.error(f"Member {member_id} or Package {package_id} not found")
            return

        # Check for memberships to accumulate time
        from datetime import datetime, timedelta, timezone

        now = datetime.now(timezone.utc)

        # Find the latest membership (by end_date) of the SAME package type
        # This ensures PT and GYM packages are independent
        latest_membership = Membership.query.join(
            GymPackage, Membership.package_id == GymPackage.id
        ).filter(
            Membership.member_id == member_id,
            GymPackage.package_type == package.package_type
        ).order_by(Membership.end_date.desc()).first()

        # Check for currently active membership of the SAME package type
        active_membership = Membership.query.join(
            GymPackage, Membership.package_id == GymPackage.id
        ).filter(
            Membership.member_id == member_id,
            Membership.active == True,
            GymPackage.package_type == package.package_type
        ).first()

        # Calculate start and end dates
        new_membership_active = False

        if latest_membership:
            # Make sure end_date is timezone-aware for comparison
            latest_end_date = latest_membership.end_date
            if latest_end_date.tzinfo is None:
                latest_end_date = latest_end_date.replace(tzinfo=timezone.utc)

            if latest_end_date > now:
                # There's a valid package (active or pending): stack new package after it
                start_date = latest_end_date
                end_date = start_date + timedelta(days=package.duration_months * 30)
                new_membership_active = False  # Will be pending until latest package expires
                stripe_logger.info(f"Creating pending membership for member {member_id}. Starts: {start_date}, Ends: {end_date}")
            else:
                # Latest package has expired: activate new package immediately
                # Deactivate old active membership if exists
                if active_membership:
                    active_membership.active = False
                start_date = now
                end_date = start_date + timedelta(days=package.duration_months * 30)
                new_membership_active = True
                stripe_logger.info(f"Old package expired. Activating new membership immediately for member {member_id}")
        else:
            # No existing package: activate immediately
            start_date = now
            end_date = start_date + timedelta(days=package.duration_months * 30)
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
            amount=package.price,
            payment_date=datetime.now(timezone.utc),
            note=f"Thanh toán gói {package.name} qua Stripe",
            status="PAID",
            txn_ref=session.id,
            paid_at=datetime.now(timezone.utc),
            raw_response=str(session)
        )
        db.session.add(payment)

        db.session.commit()

        stripe_logger.info(f"Successfully processed payment for member {member_id}, session {session.id}")

        # Send confirmation email
        try:
            from app.services.email_service import send_registration_confirmation_email
            send_registration_confirmation_email(member.user, membership, package)
        except Exception as email_error:
            stripe_logger.warning(f"Could not send email: {str(email_error)}")

    except Exception as e:
        db.session.rollback()
        stripe_logger.error(f"Error handling checkout session: {str(e)}")
        raise

