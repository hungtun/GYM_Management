from math import ceil

from flask import Blueprint, flash, render_template, request, redirect, url_for, current_app
from flask_login import login_required, current_user

from app.decorators import role_required
from app.extensions import db
from app.models import TrainingDetail, Member, TrainingPlan, PTSubscription
from app.services.trainer_services import *

trainer = Blueprint('trainer', __name__, url_prefix='/trainer')

@trainer.route('/')
@login_required
@role_required('trainer')
def dashboard():
    trainer = get_trainer_by_user_id(current_user.id)
    if not trainer:
        return "Trainer profile not found", 404
    
    stats = get_trainer_stats(trainer.id)
    
    # Lấy số lượng pending PT requests
    pending_requests_count = len(get_pending_pt_subscriptions())
    
    return render_template('trainer/dashboard.html',
                         user=current_user,
                         trainer=trainer,
                         stats=stats,
                         pending_requests_count=pending_requests_count)

@trainer.route('/members')
@login_required
@role_required('trainer')
def members():
    trainer_profile = get_trainer_by_user_id(current_user.id)
    if not trainer_profile:
        flash('Không tìm thấy hồ sơ huấn luyện viên', 'error')
        return redirect(url_for('trainer.dashboard'))

    page = request.args.get('page', 1, type=int)
    page_size = current_app.config.get('PAGE_SIZE', 6)

    # Lấy members từ PTSubscription thay vì TrainingPlan
    base_query = db.session.query(Member).join(
        PTSubscription, PTSubscription.member_id == Member.id
    ).filter(
        PTSubscription.trainer_id == trainer_profile.id,
        PTSubscription.status.in_(['active', 'pending'])
    ).distinct()

    total_members = base_query.count()
    members = base_query.order_by(Member.register_date.desc()).offset((page - 1) * page_size).limit(page_size).all()
    total_pages = max(ceil(total_members / page_size), 1)

    # Lấy PT subscriptions cho mỗi member để hiển thị trong UI
    member_subscriptions_map = {}
    for member in members:
        subscriptions = PTSubscription.query.filter_by(
            member_id=member.id,
            trainer_id=trainer_profile.id,
            status='active'
        ).all()
        member_subscriptions_map[member.id] = subscriptions

    return render_template(
        'trainer/members.html',
        members=members,
        trainer=trainer_profile,
        page=page,
        total_pages=total_pages,
        total_members=total_members,
        page_size=page_size,
        member_subscriptions_map=member_subscriptions_map
    )

@trainer.route('/plans')
@login_required
@role_required('trainer')
def plans():
    trainer_profile = get_trainer_by_user_id(current_user.id)
    if not trainer_profile:
        flash('Không tìm thấy hồ sơ huấn luyện viên', 'error')
        return redirect(url_for('trainer.dashboard'))

    page = request.args.get('page', 1, type=int)
    member_filter = request.args.get('member_id', type=int)
    page_size = current_app.config.get('PAGE_SIZE', 6)

    base_query = TrainingPlan.query.filter_by(trainer_id=trainer_profile.id).order_by(TrainingPlan.created_at.desc())
    if member_filter:
        base_query = base_query.filter(TrainingPlan.member_id == member_filter)

    total_plans = base_query.count()
    plans = base_query.offset((page - 1) * page_size).limit(page_size).all()
    total_pages = max(ceil(total_plans / page_size), 1)

    managed_members = get_trainer_members(trainer_profile.id)

    return render_template(
        'trainer/training_plans.html',
        trainer=trainer_profile,
        plans=plans,
        page=page,
        total_pages=total_pages,
        total_plans=total_plans,
        page_size=page_size,
        managed_members=managed_members,
        member_filter=member_filter
    )

@trainer.route('/profile', methods=['GET', 'POST'])
@login_required
@role_required('trainer')
def profile():
    trainer_profile = get_trainer_by_user_id(current_user.id)
    if not trainer_profile:
        flash('Không tìm thấy hồ sơ huấn luyện viên', 'error')
        return redirect(url_for('trainer.dashboard'))

    if request.method == 'POST':
        profile_data = {
            'first_name': request.form.get('first_name'),
            'last_name': request.form.get('last_name'),
            'phone': request.form.get('phone'),
            'email': request.form.get('email'),
            'gender': request.form.get('gender'),
            'birth_day': request.form.get('birth_day'),
            'specialization': request.form.get('specialization'),
            'experience_years': request.form.get('experience_years'),
            'salary': request.form.get('salary'),
        }

        update_trainer_profile(current_user.id, profile_data)
        flash('Cập nhật thông tin thành công', 'success')
        return redirect(url_for('trainer.profile'))

    stats = get_trainer_stats(trainer_profile.id)
    return render_template('trainer/profile.html', trainer=trainer_profile, user=current_user, stats=stats)

@trainer.route('/plans/create', methods=['GET', 'POST'])
@login_required
@role_required('trainer')
def create_plan():
    trainer_profile = get_trainer_by_user_id(current_user.id)
    
    if request.method == 'GET':
        all_pt_subs = PTSubscription.query.filter(
            PTSubscription.trainer_id == trainer_profile.id
        ).all()
        
        subscriptions_without_plan = []
        for sub in all_pt_subs:
            existing_plan = TrainingPlan.query.filter_by(pt_subscription_id=sub.id).first()
            if sub.status == 'active' and not existing_plan:
                subscriptions_without_plan.append(sub)
        
        if not subscriptions_without_plan:
            if all_pt_subs:
                active_subs = [s for s in all_pt_subs if s.status == 'active']
                if active_subs:
                    flash('Tất cả các subscription active của bạn đã có kế hoạch tập luyện rồi.', 'info')
                else:
                    flash('Bạn chưa có subscription PT nào ở trạng thái active. Vui lòng nhận yêu cầu PT từ trang "Yêu cầu PT chờ nhận".', 'warning')
            else:
                flash('Bạn chưa có subscription PT nào. Vui lòng nhận yêu cầu PT từ trang "Yêu cầu PT chờ nhận".', 'warning')
        
        exercises = get_all_exercises()
        selected_subscription_id = request.args.get('subscription_id')
        
        return render_template('trainer/create_plan.html',
                               pt_subscriptions=subscriptions_without_plan,
                               exercises=exercises,
                               trainer=trainer_profile,
                               selected_subscription_id=selected_subscription_id)
    if request.method == 'POST':
        pt_subscription_id = request.form.get('pt_subscription_id')
        if not pt_subscription_id:
            flash('Vui lòng chọn subscription PT','error')
            return redirect(url_for('trainer.create_plan'))
        
        # Kiểm tra subscription thuộc về trainer này
        pt_subscription = PTSubscription.query.get(pt_subscription_id)
        if not pt_subscription or pt_subscription.trainer_id != trainer_profile.id:
            flash('Subscription không hợp lệ', 'error')
            return redirect(url_for('trainer.create_plan'))
        
        exercise_ids = request.form.getlist('exercise_id[]')
        sets_list = request.form.getlist('sets[]')
        reps_list = request.form.getlist('reps[]')
        days_list = request.form.getlist('days[]')   
        valid_rows = [
           i for i in range(len(exercise_ids))
           if exercise_ids[i] and sets_list[i] and reps_list[i] and days_list[i].strip()
        ]
        if not valid_rows:
           flash('Vui lòng thêm ít nhất một bài tập đầy đủ thông tin', 'error')
           return redirect(url_for('trainer.create_plan', subscription_id=pt_subscription_id))
        MAX_DAYS_PER_WEEK = get_max_days_per_week()

        all_days = set()

        for idx in valid_rows:
            raw_days = days_list[idx]
            split_days = [day.strip() for day in raw_days.split(',') if day.strip()]
            all_days.update(split_days)

        if len(all_days) > MAX_DAYS_PER_WEEK:
            flash(f'Tổng số ngày trong tuần không được vượt quá {MAX_DAYS_PER_WEEK} ngày.', 'error')
            return redirect(url_for('trainer.create_plan', subscription_id=pt_subscription_id))

        plan = create_training_plan(pt_subscription_id)
        
        for idx in valid_rows:
           detail = TrainingDetail(
               plan_id=plan.id,
               exercise_id=exercise_ids[idx],
               sets=int(sets_list[idx]),
               reps=int(reps_list[idx]),
               days_of_week=days_list[idx].strip()
           )
           db.session.add(detail)
        db.session.commit()
        flash('Kế hoạch tập luyện đã được tạo thành công', 'success')
        return redirect(url_for('trainer.plan_detail', plan_id=plan.id))

@trainer.route('/plans/<int:plan_id>')
@login_required
@role_required('trainer')
def plan_detail(plan_id):
    trainer_profile = get_trainer_by_user_id(current_user.id)
    if not trainer_profile:
        return "Trainer profile not found", 404
    
    plan = get_training_plan_with_details(plan_id)
    if not plan or plan.trainer_id != trainer_profile.id:
        return "Không tìm thấy kế hoạch", 404

    return render_template('trainer/plan_detail.html', plan=plan, trainer=trainer_profile)

@trainer.route('/plans/<int:plan_id>/edit', methods=['GET','POST'])
@login_required
@role_required('trainer')
def edit_plan(plan_id):

    trainer_profile = get_trainer_by_user_id(current_user.id)
    if not trainer_profile:
        flash('Không tìm thấy hồ sơ huấn luyện viên', 'error')
        return redirect(url_for('trainer.dashboard'))
    
    plan = get_training_plan_with_details(plan_id)
    if not plan or plan.trainer_id != trainer_profile.id:
        flash('Không tìm thấy kế hoạch tập luyện', 'error')
        return redirect(url_for('trainer.plans'))
    
    if request.method == 'GET':
        exercises = get_all_exercises()
        return render_template('trainer/edit_plan.html',
                                plan = plan,
                               exercises = exercises,
                               trainer = trainer_profile)
    
    if request.method == 'POST':
        
        exercise_ids = request.form.getlist('exercise_id[]')
        sets_list = request.form.getlist('sets[]')
        reps_list = request.form.getlist('reps[]')
        days_list = request.form.getlist('days[]') 

        valid_rows = [
           i for i in range(len(exercise_ids))
           if exercise_ids[i] and sets_list[i] and reps_list[i] and days_list[i].strip()
        ]
        
        if not valid_rows:
           flash('Vui lòng thêm ít nhất một bài tập đầy đủ thông tin', 'error')
           exercises = get_all_exercises()
           return render_template('trainer/edit_plan.html', 
                                   plan=plan,
                                   exercises=exercises,
                                   trainer_profile=trainer_profile)
        MAX_DAYS_PER_WEEK = get_max_days_per_week()

        all_days = set()
        for idx in valid_rows:
            raw_days = days_list[idx]
            split_days = [d.strip() for d in raw_days.split(',') if d.strip()]
            all_days.update(split_days)

        if len(all_days) > MAX_DAYS_PER_WEEK:
            flash(f'Số ngày tập tối đa mỗi tuần là {MAX_DAYS_PER_WEEK}, bạn đang chọn {len(all_days)} ngày.', 'error')
            exercises = get_all_exercises()
            return render_template('trainer/edit_plan.html',
                                plan=plan,
                                exercises=exercises,
                                trainer=trainer_profile)

        delete_training_plan_details(plan_id)

        for idx in valid_rows:
           detail = TrainingDetail(
               plan_id=plan.id,
               exercise_id=int(exercise_ids[idx]),
               sets=int(sets_list[idx]),
               reps=int(reps_list[idx]),
               days_of_week=days_list[idx].strip()
           )
           db.session.add(detail)
        db.session.commit()
        flash('Kế hoạch tập luyện đã được cập nhật', 'success')
        return redirect(url_for('trainer.plan_detail', plan_id=plan.id))


@trainer.route('/plans/<int:plan_id>/delete', methods=['POST'])
@login_required
@role_required('trainer')
def delete_plan(plan_id):
    trainer_profile = get_trainer_by_user_id(current_user.id)
    if not trainer_profile:
        flash('Không tìm thấy hồ sơ huấn luyện viên', 'error')
        return redirect(url_for('trainer.dashboard'))
    
    plan = get_training_plan_with_details(plan_id)
    if not plan or plan.trainer_id != trainer_profile.id:
        flash('Không tìm thấy kế hoạch tập luyện', 'error')
        return redirect(url_for('trainer.plans'))
    
    delete_training_plan_details(plan_id)
    db.session.delete(plan)
    db.session.commit()
    
    flash('Kế hoạch tập luyện đã được xóa', 'success')
    return redirect(url_for('trainer.plans'))

@trainer.route('/pt-requests')
@login_required
@role_required('trainer')
def pt_requests():
    """Hiển thị danh sách các yêu cầu PT đang pending (chưa có trainer nhận)"""
    trainer_profile = get_trainer_by_user_id(current_user.id)
    if not trainer_profile:
        flash('Không tìm thấy hồ sơ huấn luyện viên', 'error')
        return redirect(url_for('trainer.dashboard'))
    
    page = request.args.get('page', 1, type=int)
    page_size = current_app.config.get('PAGE_SIZE', 6)
    
    # Lấy tất cả PT subscriptions đang pending (chưa có trainer)
    base_query = PTSubscription.query.filter(
        PTSubscription.trainer_id.is_(None),
        PTSubscription.status == 'pending'
    ).order_by(PTSubscription.created_at.desc())
    
    total_requests = base_query.count()
    requests = base_query.offset((page - 1) * page_size).limit(page_size).all()
    total_pages = max(ceil(total_requests / page_size), 1)
    
    return render_template(
        'trainer/pt_requests.html',
        requests=requests,
        trainer=trainer_profile,
        page=page,
        total_pages=total_pages,
        total_requests=total_requests,
        page_size=page_size
    )

@trainer.route('/pt-requests/<int:subscription_id>/accept', methods=['POST'])
@login_required
@role_required('trainer')
def accept_pt_request(subscription_id):
    """Trainer accept một PT subscription request"""
    trainer_profile = get_trainer_by_user_id(current_user.id)
    if not trainer_profile:
        flash('Không tìm thấy hồ sơ huấn luyện viên', 'error')
        return redirect(url_for('trainer.dashboard'))
    
    try:
        accept_pt_subscription(subscription_id, trainer_profile.id)
        flash('Đã nhận yêu cầu PT thành công! Bạn có thể tạo kế hoạch tập luyện cho hội viên này.', 'success')
    except ValueError as e:
        flash(str(e), 'error')
    except Exception as e:
        flash(f'Lỗi khi nhận yêu cầu: {str(e)}', 'error')
    
    return redirect(url_for('trainer.pt_requests'))