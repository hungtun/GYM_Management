import hashlib
import sys
import os
from datetime import datetime, timedelta, date

# Thêm đường dẫn thư mục gốc của ứng dụng vào hệ thống
# Giả định cấu trúc ứng dụng Flask của bạn như sau:
# project_root/
# ├── app/
# │   ├── __init__.py (khởi tạo app, db)
# │   ├── models.py
# │   ├── extensions.py (chứa db)
# └── seed.py  <- File này
#
# Nếu cấu trúc của bạn khác, hãy điều chỉnh dòng dưới đây
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


try:
    # Cần đảm bảo các import này hoạt động.
    # Thường thì Flask App instance và db sẽ được định nghĩa ở đâu đó.
    # Tôi sẽ giả định bạn có một hàm factory hoặc một cách để lấy app instance.
    from app import create_app # Thay create_app bằng hàm tạo ứng dụng của bạn
    from app.extensions import db
    from app.models import (
        Role, User, Member, Trainer, Receptionist, GymPackage,
        Membership, Payment, Exercise, TrainingPlan, TrainingDetail
    )
    from werkzeug.security import generate_password_hash
except ImportError as e:
    print(f"Lỗi khi import modules: {e}")
    print("Vui lòng kiểm tra lại cấu trúc thư mục và đường dẫn import (ví dụ: 'from app import create_app', 'from app.extensions import db').")
    exit()


def seed_data(app):
    """
    Hàm chính để seed dữ liệu vào cơ sở dữ liệu.
    """
    with app.app_context():
        print("--- BẮT ĐẦU SEED DỮ LIỆU ---")

        # Mật khẩu hash mẫu (ví dụ: "Password123")
        hashed_password = hashlib.md5("1".encode('utf-8')).hexdigest()
        # --- (Tùy chọn) XÓA DỮ LIỆU CŨ ---
        print("\n[Bước 0] Xóa dữ liệu cũ (Chỉ trong môi trường DEV/TEST)...")
        try:
            db.session.query(TrainingDetail).delete()
            db.session.query(TrainingPlan).delete()
            db.session.query(Exercise).delete()
            db.session.query(Payment).delete()
            db.session.query(Membership).delete()
            db.session.query(GymPackage).delete()
            db.session.query(Member).delete()
            db.session.query(Trainer).delete()
            db.session.query(Receptionist).delete()
            db.session.query(User).delete()
            db.session.query(Role).delete()
            db.session.commit()
            print("   -> Đã xóa dữ liệu cũ thành công.")
        except Exception as e:
            db.session.rollback()
            print(f"   -> Lỗi khi xóa dữ liệu: {e}")
            sys.exit(1)


        # --- BƯỚC 1: ROLES ---
        print("\n[Bước 1] Seed Roles...")
        role_admin = Role(name="Admin")
        role_trainer = Role(name="Trainer")
        role_member = Role(name="Member")
        role_receptionist = Role(name="Receptionist")
        db.session.add_all([role_admin, role_trainer, role_member, role_receptionist])
        db.session.commit()
        print("   -> Roles OK.")

        # --- BƯỚC 2: USERS CHUNG ---
        print("\n[Bước 2] Seed Users...")
        user_admin = User(username="admin", email="admin@gym.com", password_hash=hashed_password, first_name="Quản", last_name="Trị", role=role_admin)
        user_trainer_1 = User(username="trainer_pt", email="trainer1@gym.com", password_hash=hashed_password, first_name="Hùng", last_name="Lực", role=role_trainer)
        user_trainer_2 = User(username="trainer_yoga", email="trainer2@gym.com", password_hash=hashed_password, first_name="Mai", last_name="Sơn", role=role_trainer)
        user_receptionist = User(username="receptionist", email="receptionist@gym.com", password_hash=hashed_password, first_name="Lan", last_name="Hương", role=role_receptionist)
        user_member_1 = User(username="hoivien_a", email="member1@gym.com", password_hash=hashed_password, first_name="Thành", last_name="Đạt", gender="Male", birth_day=date(1997, 10, 25), role=role_member)
        user_member_2 = User(username="hoivien_b", email="member2@gym.com", password_hash=hashed_password, first_name="Minh", last_name="Anh", gender="Female", birth_day=date(2001, 1, 5), role=role_member)

        db.session.add_all([user_admin, user_trainer_1, user_trainer_2, user_receptionist, user_member_1, user_member_2])
        db.session.commit()
        print("   -> Users OK.")

        # --- BƯỚC 3: PROFILE CHI TIẾT ---
        print("\n[Bước 3] Seed Profiles...")
        trainer_1 = Trainer(user=user_trainer_1, specialization="Strength Training", experience_years=5, salary=20000000.00)
        trainer_2 = Trainer(user=user_trainer_2, specialization="Yoga & Flexibility", experience_years=3, salary=15000000.00)
        receptionist = Receptionist(user=user_receptionist, shift="Morning", salary=8000000.00)
        member_1 = Member(user=user_member_1, register_date=datetime.utcnow() - timedelta(days=60), status="active")
        member_2 = Member(user=user_member_2, register_date=datetime.utcnow() - timedelta(days=30), status="active")
        db.session.add_all([trainer_1, trainer_2, receptionist, member_1, member_2])
        db.session.commit()
        print("   -> Profiles OK.")

        # --- BƯỚC 4: GÓI TẬP (GYM PACKAGE) ---
        print("\n[Bước 4] Seed Gym Packages...")
        package_1m = GymPackage(name="Gói 1 tháng", duration_months=1, price=500000.00, description="Gói tập cơ bản 1 tháng")
        package_3m = GymPackage(name="Gói 3 tháng", duration_months=3, price=1200000.00, description="Gói tập 3 tháng, tiết kiệm hơn")
        package_6m = GymPackage(name="Gói 6 tháng", duration_months=6, price=2000000.00, description="Gói tập 6 tháng, ưu đãi tốt")
        package_12m = GymPackage(name="Gói 12 tháng", duration_months=12, price=3500000.00, description="Gói tập 1 năm, giá tốt nhất")
        db.session.add_all([package_1m, package_3m, package_6m, package_12m])
        db.session.commit()
        print("   -> Gym Packages OK.")

        # --- BƯỚC 5: ĐĂNG KÝ GÓI (MEMBERSHIP) ---
        print("\n[Bước 5] Seed Memberships...")
        start_date_1 = datetime.utcnow() - timedelta(days=60)
        end_date_1 = start_date_1 + timedelta(days=365) # 12 months
        start_date_2 = datetime.utcnow() - timedelta(days=30)
        end_date_2 = start_date_2 + timedelta(days=90) # 3 months

        membership_1 = Membership(member=member_1, package=package_12m, start_date=start_date_1, end_date=end_date_1, active=True)
        membership_2 = Membership(member=member_2, package=package_3m, start_date=start_date_2, end_date=end_date_2, active=True)

        db.session.add_all([membership_1, membership_2])
        db.session.commit()
        print("   -> Memberships OK.")

        # --- BƯỚC 6: THANH TOÁN ---
        print("\n[Bước 6] Seed Payments...")
        payment_1 = Payment(member=member_1, amount=package_12m.price, payment_date=start_date_1, note=f"Payment for {package_12m.name}")
        payment_2 = Payment(member=member_2, amount=package_3m.price, payment_date=start_date_2, note=f"Payment for {package_3m.name}")
        db.session.add_all([payment_1, payment_2])
        db.session.commit()
        print("   -> Payments OK.")

        # --- BƯỚC 7: BÀI TẬP (EXERCISE) ---
        print("\n[Bước 7] Seed Exercises...")
        exercise_squat = Exercise(name="Squat", description="Compound exercise for legs and core.")
        exercise_bench = Exercise(name="Bench Press", description="Main chest exercise.")
        exercise_deadlift = Exercise(name="Deadlift", description="Full body strength exercise.")
        db.session.add_all([exercise_squat, exercise_bench, exercise_deadlift])
        db.session.commit()
        print("   -> Exercises OK.")

        # --- BƯỚC 8 & 9: KẾ HOẠCH TẬP LUYỆN ---
        print("\n[Bước 8 & 9] Seed Training Plans and Details...")
        training_plan_1 = TrainingPlan(trainer=trainer_1, member=member_1, date_created=datetime.utcnow() - timedelta(days=15))
        db.session.add(training_plan_1)
        db.session.flush()  # Dùng flush thay vì commit để giữ transaction

        # Tạo TrainingDetail và add vào session
        detail_1 = TrainingDetail(plan=training_plan_1, exercise=exercise_squat, sets=4, reps=10, days_of_week="Mon, Thu")
        detail_2 = TrainingDetail(plan=training_plan_1, exercise=exercise_bench, sets=3, reps=8, days_of_week="Mon, Thu")
        detail_3 = TrainingDetail(plan=training_plan_1, exercise=exercise_deadlift, sets=3, reps=5, days_of_week="Fri")

        db.session.add_all([detail_1, detail_2, detail_3])
        db.session.commit()
        print("   -> Training Plans & Details OK.")

        print("\n--- ✅ SEED DỮ LIỆU HOÀN TẤT! ---")
        print("\nThông tin đăng nhập mẫu:")
        print("  - Admin: admin/Password123")
        print("  - Hội viên 1: hoivien_a/Password123")


if __name__ == '__main__':
    # THAY ĐỔI: Thay 'app_name' bằng module/instance Flask của bạn
    # Ví dụ: nếu hàm factory của bạn là create_app(), hãy dùng như dưới đây.
    app = create_app()
    seed_data(app)