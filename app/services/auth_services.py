from app.models import User
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


