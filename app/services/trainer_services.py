from app.models import Trainer, Member, TrainingPlan, TrainingDetail, SystemSetting
from app.extensions import db
from sqlalchemy.orm import joinedload


def get_trainer_by_user_id(user_id):
    return Trainer.query.filter_by(user_id=user_id).first()
def get_trainer_stats(trainer_id):
    total_members = get_trainer_members(trainer_id).__len__()

    tolal_plans = TrainingPlan.query.filter_by(trainer_id=trainer_id).count()

    recent_plans = TrainingPlan.query.filter_by(trainer_id=trainer_id).order_by(TrainingPlan.created_at.desc()).limit(5).all()

    return {
        'total_members': total_members,
        'total_plans': tolal_plans,
        'recent_plans': recent_plans
    }

def get_trainer_members(trainer_id):
    members = db.session.query(Member).join(
        TrainingPlan, TrainingPlan.member_id == Member.id
    ).filter(TrainingPlan.trainer_id == trainer_id).distinct().all()
    return members

def get_training_plans_by_trainer(trainer_id):
    return TrainingPlan.query.filter_by(trainer_id=trainer_id).order_by(TrainingPlan.created_at.desc()).all()

def create_training_plan(trainer_id, member_id):
    new_plan = TrainingPlan(trainer_id=trainer_id, member_id=member_id)
    db.session.add(new_plan)
    db.session.commit()
    return new_plan

def update_training_plan(plan_id, **kwargs):
    plan = TrainingPlan.query.get(plan_id)
    if not plan:
        return None
    for key, value in kwargs.items():
        setattr(plan, key, value)
    db.session.commit()
    return plan

def delete_training_plan_details(plan_id):
    details = TrainingDetail.query.filter_by(plan_id=plan_id).all()
    for detail in details:
        db.session.delete(detail)
    db.session.commit()

def get_training_plan_by_id(plan_id):
    return TrainingPlan.query.filter_by(id=plan_id).first()

def get_all_exercises():
    from app.models import Exercise
    return Exercise.query.all()

def get_training_plan_with_details(plan_id):
    return (
        TrainingPlan.query
        .options(
            joinedload(TrainingPlan.details).joinedload(TrainingDetail.exercise)
        )
        .filter_by(id=plan_id)
        .first()
    )

def get_max_days_per_week():
    setting = SystemSetting.query.filter_by(key='MAX_DAYS_PER_WEEK').first()
    return int(setting.value)
