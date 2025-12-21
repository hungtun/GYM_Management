from app.models import Trainer, Member, TrainingPlan, TrainingDetail, SystemSetting, PTSubscription
from app.extensions import db


def get_trainer_by_user_id(user_id):
    return Trainer.query.filter_by(user_id=user_id).first()

def get_trainer_stats(trainer_id):
    total_members = get_trainer_members(trainer_id).__len__()

    total_subscriptions = PTSubscription.query.filter_by(trainer_id=trainer_id).count()

    total_plans = TrainingPlan.query.filter_by(trainer_id=trainer_id).count()

    recent_subscriptions = PTSubscription.query.filter_by(trainer_id=trainer_id).order_by(PTSubscription.created_at.desc()).limit(5).all()

    return {
        'total_members': total_members,
        'total_subscriptions': total_subscriptions,
        'total_plans': total_plans,
        'recent_subscriptions': recent_subscriptions
    }

def get_trainer_members(trainer_id):
    members = db.session.query(Member).join(
        PTSubscription, PTSubscription.member_id == Member.id
    ).filter(
        PTSubscription.trainer_id == trainer_id,
        PTSubscription.status.in_(['active', 'pending'])  
    ).distinct().all()
    return members

def get_trainer_available_members(trainer_id):

    members = db.session.query(Member).join(
        PTSubscription, PTSubscription.member_id == Member.id
    ).filter(
        PTSubscription.trainer_id == trainer_id,
        PTSubscription.status == 'active'
    ).distinct().all()
    
    return sorted(members, key=lambda m: m.register_date, reverse=True)

def get_training_plans_by_trainer(trainer_id):
    return TrainingPlan.query.filter_by(trainer_id=trainer_id).order_by(TrainingPlan.created_at.desc()).all()

def create_training_plan(pt_subscription_id):
    pt_subscription = PTSubscription.query.get(pt_subscription_id)
    if not pt_subscription:
        raise ValueError("PTSubscription không tồn tại")
    
    if not pt_subscription.trainer_id:
        raise ValueError("PTSubscription chưa có trainer")
    
    existing_plan = TrainingPlan.query.filter_by(pt_subscription_id=pt_subscription_id).first()
    if existing_plan:
        return existing_plan
    
    new_plan = TrainingPlan(
        pt_subscription_id=pt_subscription_id,
        trainer_id=pt_subscription.trainer_id,
        member_id=pt_subscription.member_id
    )
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
    return TrainingPlan.query.filter_by(id=plan_id).first()

def get_max_days_per_week(default=6):
    setting = SystemSetting.query.filter_by(key='MAX_DAYS_PER_WEEK').first()
    if not setting:
        return default
    try:
        return int(setting.value)
    except (ValueError, TypeError):
        return default

def get_pending_pt_subscriptions():
    return PTSubscription.query.filter_by(
        trainer_id=None,
        status='pending'
    ).order_by(PTSubscription.created_at.desc()).all()

def get_pt_subscriptions_by_trainer(trainer_id):
    return PTSubscription.query.filter_by(
        trainer_id=trainer_id
    ).order_by(PTSubscription.created_at.desc()).all()

def accept_pt_subscription(subscription_id, trainer_id):
    subscription = PTSubscription.query.get(subscription_id)
    if not subscription:
        raise ValueError("PTSubscription không tồn tại")
    
    if subscription.trainer_id is not None:
        raise ValueError("PTSubscription này đã có trainer")
    
    if subscription.status != 'pending':
        raise ValueError("PTSubscription không ở trạng thái pending")
    
    from datetime import datetime, timezone, timedelta
    
    now = datetime.now(timezone.utc)
    subscription.trainer_id = trainer_id
    subscription.status = 'active'
    subscription.start_date = now  
    
    if subscription.pt_package:
        subscription.end_date = now + timedelta(days=subscription.pt_package.duration_months * 30)
    
    subscription.updated_at = now
    
    db.session.commit()
    return subscription
