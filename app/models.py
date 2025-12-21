from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy import Integer, String
from app.extensions import db
from datetime import date, time, datetime, timezone
from flask_admin.contrib.sqla import ModelView
from sqlalchemy.orm import relationship, backref
from flask_login import UserMixin

class BaseModel(db.Model):
    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

# ===== BẢNG ROLE =====
class Role(BaseModel):
    name = db.Column(db.String(50), unique=True, nullable=False)
    users = db.relationship("User", back_populates="role")

    def __repr__(self):
        return self.name


# ===== BẢNG USER CHUNG =====
class User(UserMixin, BaseModel):
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(60))
    last_name = db.Column(db.String(60))
    gender = db.Column(db.String(10))
    birth_day = db.Column(db.Date)
    phone = db.Column(db.String(20))
    avatar_url = db.Column(db.String(255))
    join_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    role_id = db.Column(db.Integer, db.ForeignKey("role.id"))
    role = db.relationship("Role", back_populates="users")

    member_profile = db.relationship("Member", uselist=False, back_populates="user", cascade="all, delete-orphan")
    trainer_profile = db.relationship("Trainer", uselist=False, back_populates="user", cascade="all, delete-orphan")
    receptionist_profile = db.relationship("Receptionist", uselist=False, back_populates="user", cascade="all, delete-orphan")


# ===== HỘI VIÊN =====
class Member(BaseModel):
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    register_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    status = db.Column(db.String(20), default="active")

    user = db.relationship("User", back_populates="member_profile")
    memberships = db.relationship("Membership", back_populates="member", cascade="all, delete-orphan")
    payments = db.relationship("Payment", back_populates="member", cascade="all, delete-orphan")
    pt_subscriptions = db.relationship("PTSubscription", back_populates="member")  


# ===== HUẤN LUYỆN VIÊN =====
class Trainer(BaseModel):
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    specialization = db.Column(db.String(100))
    experience_years = db.Column(db.Integer)
    salary = db.Column(db.Float)

    user = db.relationship("User", back_populates="trainer_profile")
    training_plans = db.relationship("TrainingPlan", back_populates="trainer")
    pt_subscriptions = db.relationship("PTSubscription", back_populates="trainer")  


# ===== LỄ TÂN =====
class Receptionist(BaseModel):
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    shift = db.Column(db.String(20))
    salary = db.Column(db.Float)

    user = db.relationship("User", back_populates="receptionist_profile")


# ===== GÓI TẬP =====
class GymPackage(BaseModel):
    name = db.Column(db.String(50), nullable=False)
    duration_months = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255))

    memberships = db.relationship("Membership", back_populates="package")

# ===== GÓI PT (PERSONAL TRAINER PACKAGE) =====
class PTPackage(BaseModel):
    name = db.Column(db.String(50), nullable=False)
    duration_months = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255))

    subscriptions = db.relationship("PTSubscription", back_populates="pt_package")

# ===== ĐĂNG KÝ GÓI (THẺ HỘI VIÊN) =====
class Membership(BaseModel):
    member_id = db.Column(db.Integer, db.ForeignKey("member.id"), nullable=False)
    package_id = db.Column(db.Integer, db.ForeignKey("gym_package.id"), nullable=False)
    start_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    end_date = db.Column(db.DateTime)
    active = db.Column(db.Boolean, default=True)

    member = db.relationship("Member", back_populates="memberships")
    package = db.relationship("GymPackage", back_populates="memberships")

# ===== ĐĂNG KÝ GÓI PT (PERSONAL TRAINER SUBSCRIPTION) =====
class PTSubscription(BaseModel):
    member_id = db.Column(db.Integer, db.ForeignKey("member.id"), nullable=False)
    pt_package_id = db.Column(db.Integer, db.ForeignKey("pt_package.id"), nullable=False)
    trainer_id = db.Column(db.Integer, db.ForeignKey("trainer.id"), nullable=True) 
    
    start_date = db.Column(db.DateTime, nullable=True)  # Sẽ được set khi trainer accept
    end_date = db.Column(db.DateTime, nullable=True)  # Sẽ được tính khi trainer accept
    active = db.Column(db.Boolean, default=True)
    
    status = db.Column(db.String(20), default="pending")  # pending, active, completed, cancelled
    notes = db.Column(db.Text)  # Ghi chú từ member hoặc trainer
    
    member = db.relationship("Member", back_populates="pt_subscriptions")
    pt_package = db.relationship("PTPackage", back_populates="subscriptions")
    trainer = db.relationship("Trainer", back_populates="pt_subscriptions")
    training_plans = db.relationship("TrainingPlan", back_populates="pt_subscription", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"PTSubscription(member={self.member_id}, package={self.pt_package_id}, status={self.status})"

# ===== THANH TOÁN =====
class Payment(BaseModel):
    member_id = db.Column(db.Integer, db.ForeignKey("member.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    note = db.Column(db.String(255))


    status = db.Column(db.String(20), default="PAID")
    txn_ref = db.Column(db.String(100), unique=True)
    paid_at = db.Column(db.DateTime)
    raw_response = db.Column(db.Text)

    member = db.relationship("Member", back_populates="payments")


# ===== BÀI TẬP =====
class Exercise(BaseModel):
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))


# ===== KẾ HOẠCH TẬP LUYỆN =====
class TrainingPlan(BaseModel):
    pt_subscription_id = db.Column(db.Integer, db.ForeignKey("pt_subscription.id"), nullable=False)
    trainer_id = db.Column(db.Integer, db.ForeignKey("trainer.id"), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey("member.id"), nullable=False)

    # Relationships - Thêm pt_subscription
    pt_subscription = db.relationship("PTSubscription", back_populates="training_plans")
    trainer = db.relationship("Trainer", back_populates="training_plans")
    member = db.relationship("Member")
    details = db.relationship("TrainingDetail", back_populates="plan", cascade="all, delete-orphan")


# ===== CHI TIẾT KẾ HOẠCH TẬP =====
class TrainingDetail(BaseModel):
    plan_id = db.Column(db.Integer, db.ForeignKey("training_plan.id"))
    exercise_id = db.Column(db.Integer, db.ForeignKey("exercise.id"))
    sets = db.Column(db.Integer)
    reps = db.Column(db.Integer)
    days_of_week = db.Column(db.String(50))

    plan = db.relationship("TrainingPlan", back_populates="details")
    exercise = db.relationship("Exercise")

class SystemSetting(BaseModel):
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f"{self.key} = {self.value}"