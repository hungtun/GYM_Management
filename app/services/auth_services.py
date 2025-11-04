from app.models import User,Role,Member
from config import Config
from app.extensions import db
import hashlib
from datetime import datetime
from flask import jsonify

def check_login(user_name, password):
    if user_name and password:
        password_hash = str(hashlib.md5((password).strip().encode('utf-8')).hexdigest())

        return User.query.filter(User.username.__eq__(user_name.strip()),
                                User.password_hash.__eq__(password_hash)).first()

def get_user_account_by_id(user_id):
    return User.query.get(user_id)

def add_user_default(first_name, last_name, user_name, password, email, phone_number, gender, birth_day, role_id=None):
    password_hash = hashlib.md5(password.strip().encode("utf-8")).hexdigest()

    if role_id:
        role = Role.query.get(role_id)
    else:
        role = Role.query.filter_by(name="member").first()

    # Convert birth_day to date if it's datetime
    if isinstance(birth_day, datetime):
        birth_date = birth_day.date()
    else:
        birth_date = birth_day

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

    if role and role.name.lower() == 'member':
        member = Member(user_id=user.id)
        db.session.add(member)
    elif role and role.name.lower() == 'trainer':
        from app.models import Trainer
        trainer = Trainer(user_id=user.id)
        db.session.add(trainer)
    elif role and role.name.lower() == 'receptionist':
        from app.models import Receptionist
        receptionist = Receptionist(user_id=user.id)
        db.session.add(receptionist)

    db.session.commit()
    return user
