from flask_admin import Admin, BaseView, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask import request, redirect, url_for, render_template, jsonify, flash
from flask_login import current_user, logout_user
from wtforms import PasswordField, StringField, SelectField, DateField
from wtforms.validators import DataRequired, Length
from app.extensions import db
from app.models import (
    User, Role, Member, Trainer, Receptionist,
    GymPackage, Membership, Payment, Exercise,
    TrainingPlan, TrainingDetail
)
from app.decorators import role_required
from datetime import datetime
import hashlib


class AdminModelView(ModelView):
    def is_accessible(self):
        if not current_user.is_authenticated:
            return False
        role_name = None
        if current_user.role and current_user.role.name:
            role_name = current_user.role.name.lower()
        return role_name == 'admin'

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('auth.user_login'))


class UserView(AdminModelView):
    """
    Custom view cho User management - Có thể tạo user với password
    """
    column_list = ['id', 'username', 'email', 'first_name', 'last_name', 'phone', 'role', 'join_date']
    column_searchable_list = ['username', 'email', 'first_name', 'last_name']
    column_filters = ['role', 'gender', 'birth_day']
    column_labels = {
        'username': 'Tên đăng nhập',
        'email': 'Email',
        'first_name': 'Họ',
        'last_name': 'Tên',
        'phone': 'Số điện thoại',
        'role': 'Vai trò',
        'join_date': 'Ngày tham gia',
        'birth_day': 'Ngày sinh',
        'password': 'Mật khẩu'
    }
    column_formatters = {
        'role': lambda view, context, model, name: model.role.name if model.role else 'Chưa có vai trò'
    }
    form_excluded_columns = ['password_hash', 'member_profile', 'trainer_profile', 'receptionist_profile', 'join_date']
    form_extra_fields = {
        'password': PasswordField('Mật khẩu', validators=[Length(min=6, message='Mật khẩu phải có ít nhất 6 ký tự')]),
    }
    form_args = {
        'role': {
            'query_factory': lambda: Role.query.order_by(Role.name)
        }
    }
    
    def on_model_change(self, form, model, is_created):
        if is_created:
            if form.password.data:
                password = form.password.data.strip()
                if len(password) < 6:
                    raise ValueError('Mật khẩu phải có ít nhất 6 ký tự')
                model.password_hash = hashlib.md5(password.encode('utf-8')).hexdigest()
            else:
                raise ValueError('Vui lòng nhập mật khẩu khi tạo tài khoản mới')
            
            # Set join_date nếu chưa có
            if not model.join_date:
                model.join_date = datetime.utcnow()
            
            # Tạo profile dựa trên role
            if model.role and model.role.name:
                role_name = model.role.name.lower()
                db.session.flush()  # Đảm bảo user có ID
                
                if role_name == 'member':
                    member = Member(user_id=model.id)
                    db.session.add(member)
                elif role_name == 'trainer':
                    trainer = Trainer(user_id=model.id)
                    db.session.add(trainer)
                elif role_name == 'receptionist':
                    receptionist = Receptionist(user_id=model.id)
                    db.session.add(receptionist)
        else:
            # Khi cập nhật, chỉ hash password nếu có thay đổi
            if form.password.data:
                password = form.password.data.strip()
                if len(password) >= 6:
                    model.password_hash = hashlib.md5(password.encode('utf-8')).hexdigest()


class MemberView(AdminModelView):
    column_list = ['id', 'user', 'register_date', 'status']
    column_searchable_list = ['user.username', 'user.first_name', 'user.last_name', 'user.email']
    column_filters = ['status', 'register_date']
    column_labels = {
        'user': 'Người dùng',
        'register_date': 'Ngày đăng ký',
        'status': 'Trạng thái'
    }


class TrainerView(AdminModelView):
    """
    View quản lý huấn luyện viên
    """
    column_list = ['id', 'user', 'specialization', 'experience_years', 'salary']
    column_searchable_list = ['user.username', 'user.first_name', 'user.last_name', 'specialization']
    column_labels = {
        'user': 'Người dùng',
        'specialization': 'Chuyên môn',
        'experience_years': 'Số năm kinh nghiệm',
        'salary': 'Lương'
    }


class ReceptionistView(AdminModelView):
    column_list = ['id', 'user', 'shift', 'salary']
    column_searchable_list = ['user.username', 'user.first_name', 'user.last_name']
    column_filters = ['shift']
    column_labels = {
        'user': 'Người dùng',
        'shift': 'Ca làm việc',
        'salary': 'Lương'
    }


class GymPackageView(AdminModelView):
    column_list = ['id', 'name', 'duration_months', 'price', 'description']
    column_searchable_list = ['name', 'description']
    column_filters = ['duration_months', 'price']
    column_labels = {
        'name': 'Tên gói',
        'duration_months': 'Thời hạn (tháng)',
        'price': 'Giá',
        'description': 'Mô tả'
    }


class MembershipView(AdminModelView):
    column_list = ['id', 'member', 'package', 'start_date', 'end_date', 'active']
    column_searchable_list = ['member.user.username', 'package.name']
    column_filters = ['active', 'start_date', 'end_date']
    column_labels = {
        'member': 'Hội viên',
        'package': 'Gói tập',
        'start_date': 'Ngày bắt đầu',
        'end_date': 'Ngày kết thúc',
        'active': 'Hoạt động'
    }


class PaymentView(AdminModelView):
    column_list = ['id', 'member', 'amount', 'payment_date', 'note']
    column_searchable_list = ['member.user.username', 'note']
    column_filters = ['payment_date']
    column_labels = {
        'member': 'Hội viên',
        'amount': 'Số tiền',
        'payment_date': 'Ngày thanh toán',
        'note': 'Ghi chú'
    }


class ExerciseView(AdminModelView):
    column_list = ['id', 'name', 'description']
    column_searchable_list = ['name', 'description']
    column_labels = {
        'name': 'Tên bài tập',
        'description': 'Mô tả'
    }


class TrainingPlanView(AdminModelView):
    column_list = ['id', 'trainer', 'member']
    column_searchable_list = ['trainer.user.username', 'member.user.username']
    column_filters = ['created_at']
    column_labels = {
        'trainer': 'Huấn luyện viên',
        'member': 'Hội viên',
        'created_at': 'Ngày tạo'
    }


class AdminLogoutView(BaseView):
    @expose('/')
    def index(self):
        logout_user()
        return redirect(url_for('auth.user_login'))


class MyAdminIndexView(AdminIndexView):
    def __init__(self, *args, **kwargs):
        super(MyAdminIndexView, self).__init__(*args, **kwargs)
        self.endpoint = 'admin'
    
    @role_required('admin')
    @expose('/')
    def index(self):
        # Statistics
        total_members = Member.query.count()
        total_trainers = Trainer.query.count()
        total_packages = GymPackage.query.count()
        active_memberships = Membership.query.filter_by(active=True).count()
        
        stats = {
            'total_members': total_members,
            'total_trainers': total_trainers,
            'total_packages': total_packages,
            'active_memberships': active_memberships
        }
        
        return self.render('admin/index.html', stats=stats)

class RoleView(AdminModelView):
    column_list = ['id', 'name']
    column_searchable_list = ['name']
    column_labels = {
        'name': 'Tên vai trò',
    }


def init_admin(app):
    admin = Admin(
        app,
        name='GYM Beta Admin',
        index_view=MyAdminIndexView(name='Trang chủ', endpoint='admin', url='/admin')
    )
    
    # Add views với endpoint name rõ ràng
    admin.add_view(UserView(User, db.session, name='Người dùng', endpoint='admin_user', category='Quản lý người dùng'))
    admin.add_view(RoleView(Role, db.session, name='Vai trò', endpoint='admin_role', category='Quản lý người dùng'))
    admin.add_view(MemberView(Member, db.session, name='Hội viên', endpoint='admin_member', category='Quản lý người dùng'))
    admin.add_view(TrainerView(Trainer, db.session, name='Huấn luyện viên', endpoint='admin_trainer', category='Quản lý người dùng'))
    admin.add_view(ReceptionistView(Receptionist, db.session, name='Lễ tân', endpoint='admin_receptionist', category='Quản lý người dùng'))
    
    admin.add_view(GymPackageView(GymPackage, db.session, name='Gói tập', endpoint='admin_package', category='Quản lý dịch vụ'))
    admin.add_view(MembershipView(Membership, db.session, name='Thẻ hội viên', endpoint='admin_membership', category='Quản lý dịch vụ'))
    admin.add_view(PaymentView(Payment, db.session, name='Thanh toán', endpoint='admin_payment', category='Quản lý dịch vụ'))
    
    admin.add_view(ExerciseView(Exercise, db.session, name='Bài tập', endpoint='admin_exercise', category='Quản lý tập luyện'))
    admin.add_view(TrainingPlanView(TrainingPlan, db.session, name='Kế hoạch tập', endpoint='admin_training_plan', category='Quản lý tập luyện'))
    admin.add_view(ModelView(TrainingDetail, db.session, name='Chi tiết kế hoạch', endpoint='admin_training_detail', category='Quản lý tập luyện'))
    
    admin.add_view(AdminLogoutView(name='Đăng xuất', endpoint='admin_logout', category='Tiện ích'))
    
    return admin




