from flask import render_template
from flask_mail import Mail, Message
import logging
import re

mail = Mail()

# Setup logging for email service
email_logger = logging.getLogger('email_service')
email_logger.setLevel(logging.INFO)

def init_email(app):
    """Initialize Flask-Mail with app configuration"""
    try:
        mail.init_app(app)
        email_logger.info("Email service initialized successfully")

        # Test email configuration
        if app.config.get('MAIL_USERNAME') and app.config.get('MAIL_USERNAME') != 'your-email@gmail.com':
            email_logger.info(f"SMTP Server: {app.config.get('MAIL_SERVER')}:{app.config.get('MAIL_PORT')}")
            email_logger.info(f"SMTP User: {app.config.get('MAIL_USERNAME')}")
        else:
            email_logger.warning("SMTP credentials not configured. Please update config.py")
    except Exception as e:
        email_logger.error(f"Failed to initialize email service: {str(e)}")
        raise

def validate_email(email):
    """
    Validate email format

    Args:
        email: Email address to validate

    Returns:
        bool: True if valid, False otherwise
    """
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def send_registration_confirmation_email(user, membership, package):
    """
    Gửi email xác nhận đăng ký thành viên

    Args:
        user: User object
        membership: Membership object
        package: GymPackage object

    Returns:
        bool: True if sent successfully, False otherwise
    """
    if not user or not user.email:
        email_logger.warning("Cannot send email: User or email is missing")
        return False

    if not validate_email(user.email):
        email_logger.warning(f"Invalid email format: {user.email}")
        return False

    try:
        msg = Message(
            subject='Xác nhận đăng ký thành viên GYM Beta',
            recipients=[user.email],
            html=render_template(
                'emails/registration_confirmation.html',
                user=user,
                membership=membership,
                package=package
            )
        )

        mail.send(msg)
        email_logger.info(f"Registration confirmation email sent successfully to: {user.email}")
        return True

    except Exception as e:
        email_logger.error(f"Failed to send registration confirmation email to {user.email}: {str(e)}")
        # Không raise exception để không ảnh hưởng đến flow chính
        return False


