from datetime import datetime

from app.extensions import db
from app.models import User
from app.services.trainer_services import get_trainer_stats


def get_user_profile_context(user):
    role = None
    extra = {}
    stats = None

    if user.trainer_profile:
        role = 'trainer'
        trainer = user.trainer_profile
        extra = {
            'specialization': trainer.specialization,
            'experience_years': trainer.experience_years,
            'salary': trainer.salary
        }
        stats = get_trainer_stats(trainer.id)
    elif user.member_profile:
        role = 'member'
        member = user.member_profile
        extra = {
            'status': member.status,
            'register_date': member.register_date
        }
    elif user.receptionist_profile:
        role = 'receptionist'
        receptionist = user.receptionist_profile
        extra = {
            'shift': receptionist.shift,
            'salary': receptionist.salary
        }
    elif user.role and user.role.name:
        role = user.role.name.lower()

    return {
        'role': role,
        'extra': extra,
        'stats': stats
    }


def update_user_profile(user, form_data):
    user.first_name = form_data.get('first_name') or user.first_name
    user.last_name = form_data.get('last_name') or user.last_name
    user.phone = form_data.get('phone') or user.phone
    user.gender = form_data.get('gender') or user.gender

    email = form_data.get('email')
    if email:
        user.email = email

    birth_day = form_data.get('birth_day')
    if birth_day:
        try:
            user.birth_day = datetime.strptime(birth_day, '%Y-%m-%d').date()
        except ValueError:
            pass

    avatar_url = form_data.get('avatar_url')
    if avatar_url:
        user.avatar_url = avatar_url

    # Trainer-specific safe fields
    if user.trainer_profile:
        trainer = user.trainer_profile
        trainer.specialization = form_data.get('specialization') or trainer.specialization
        experience = form_data.get('experience_years')
        if experience not in (None, ''):
            try:
                trainer.experience_years = int(experience)
            except ValueError:
                pass
        # Salary is sensitive → do not update unless explicitly allowed

    db.session.commit()
    return user

