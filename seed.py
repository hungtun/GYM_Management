import hashlib
import sys
import os
from datetime import datetime, timedelta, date, timezone

# Thêm đường dẫn thư mục gốc của ứng dụng vào hệ thống
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from app import create_app
    from app.extensions import db
    from app.models import (
        Role, User, Member, Trainer, Receptionist, GymPackage, PTPackage,
        Membership, PTSubscription, Payment, Exercise, TrainingPlan, TrainingDetail,
        SystemSetting
    )
except ImportError as e:
    print(f"Lỗi khi import modules: {e}")
    print("Vui lòng kiểm tra lại cấu trúc thư mục và đường dẫn import.")
    exit()


def seed_data(app):
    """
    Hàm chính để seed dữ liệu vào cơ sở dữ liệu.
    """
    with app.app_context():
        print("--- BẮT ĐẦU SEED DỮ LIỆU ---")

        # Mật khẩu hash mẫu (password: "1")
        hashed_password = hashlib.md5("1".encode('utf-8')).hexdigest()
        
        # --- XÓA DỮ LIỆU CŨ ---
        print("\n[Bước 0] Xóa dữ liệu cũ...")
        try:
            db.session.query(TrainingDetail).delete()
            db.session.query(TrainingPlan).delete()
            db.session.query(PTSubscription).delete()
            db.session.query(Exercise).delete()
            db.session.query(Payment).delete()
            db.session.query(Membership).delete()
            db.session.query(PTPackage).delete()
            db.session.query(GymPackage).delete()
            db.session.query(SystemSetting).delete()
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
        user_admin = User(
            username="admin", email="admin@gym.com", password_hash=hashed_password,
            first_name="Quản", last_name="Trị", phone="0901234567", role=role_admin
        )
        user_trainer_1 = User(
            username="trainer_pt", email="trainer1@gym.com", password_hash=hashed_password,
            first_name="Hùng", last_name="Lực", phone="0901234568", gender="Male",
            birth_day=date(1990, 5, 15), role=role_trainer
        )
        user_trainer_2 = User(
            username="trainer_yoga", email="trainer2@gym.com", password_hash=hashed_password,
            first_name="Mai", last_name="Sơn", phone="0901234569", gender="Female",
            birth_day=date(1992, 8, 20), role=role_trainer
        )
        user_trainer_3 = User(
            username="trainer_cardio", email="trainer3@gym.com", password_hash=hashed_password,
            first_name="Nam", last_name="Anh", phone="0901234570", gender="Male",
            birth_day=date(1988, 3, 10), role=role_trainer
        )
        user_receptionist = User(
            username="receptionist", email="receptionist@gym.com", password_hash=hashed_password,
            first_name="Lan", last_name="Hương", phone="0901234571", gender="Female",
            birth_day=date(1995, 12, 5), role=role_receptionist
        )
        user_member_1 = User(
            username="hoivien_a", email="member1@gym.com", password_hash=hashed_password,
            first_name="Thành", last_name="Đạt", phone="0901234572", gender="Male",
            birth_day=date(1997, 10, 25), role=role_member
        )
        user_member_2 = User(
            username="hoivien_b", email="member2@gym.com", password_hash=hashed_password,
            first_name="Minh", last_name="Anh", phone="0901234573", gender="Female",
            birth_day=date(2001, 1, 5), role=role_member
        )
        user_member_3 = User(
            username="hoivien_c", email="member3@gym.com", password_hash=hashed_password,
            first_name="Tuấn", last_name="Minh", phone="0901234574", gender="Male",
            birth_day=date(1995, 7, 18), role=role_member
        )
        user_member_4 = User(
            username="hoivien_d", email="member4@gym.com", password_hash=hashed_password,
            first_name="Hương", last_name="Lan", phone="0901234575", gender="Female",
            birth_day=date(1999, 4, 22), role=role_member
        )
        user_member_5 = User(
            username="hoivien_e", email="member5@gym.com", password_hash=hashed_password,
            first_name="Đức", last_name="Anh", phone="0901234576", gender="Male",
            birth_day=date(2000, 9, 30), role=role_member
        )

        db.session.add_all([
            user_admin, user_trainer_1, user_trainer_2, user_trainer_3,
            user_receptionist, user_member_1, user_member_2, user_member_3,
            user_member_4, user_member_5
        ])
        db.session.commit()
        print("   -> Users OK.")

        # --- BƯỚC 3: PROFILE CHI TIẾT ---
        print("\n[Bước 3] Seed Profiles...")
        trainer_1 = Trainer(
            user=user_trainer_1, specialization="Strength Training",
            experience_years=5, salary=20000000.00
        )
        trainer_2 = Trainer(
            user=user_trainer_2, specialization="Yoga & Flexibility",
            experience_years=3, salary=15000000.00
        )
        trainer_3 = Trainer(
            user=user_trainer_3, specialization="Cardio & Weight Loss",
            experience_years=4, salary=18000000.00
        )
        receptionist = Receptionist(
            user=user_receptionist, shift="Morning", salary=8000000.00
        )
        
        # Tạo members với các ngày đăng ký khác nhau để test reports
        now = datetime.now(timezone.utc)
        member_1 = Member(
            user=user_member_1,
            register_date=now - timedelta(days=180),
            status="active"
        )
        member_2 = Member(
            user=user_member_2,
            register_date=now - timedelta(days=90),
            status="active"
        )
        member_3 = Member(
            user=user_member_3,
            register_date=now - timedelta(days=60),
            status="active"
        )
        member_4 = Member(
            user=user_member_4,
            register_date=now - timedelta(days=30),
            status="active"
        )
        member_5 = Member(
            user=user_member_5,
            register_date=now - timedelta(days=15),
            status="active"
        )
        
        db.session.add_all([
            trainer_1, trainer_2, trainer_3, receptionist,
            member_1, member_2, member_3, member_4, member_5
        ])
        db.session.commit()
        print("   -> Profiles OK.")

        # --- BƯỚC 4: GÓI TẬP (GYM PACKAGE) ---
        print("\n[Bước 4] Seed Gym Packages...")
        # Gym packages (chỉ cho GYM, không có package_type nữa)
        package_1m = GymPackage(name="Gói 1 tháng", duration_months=1, price=500000.00, description="Gói tập cơ bản 1 tháng")
        package_3m = GymPackage(name="Gói 3 tháng", duration_months=3, price=1200000.00, description="Gói tập 3 tháng, tiết kiệm hơn")
        package_6m = GymPackage(name="Gói 6 tháng", duration_months=6, price=2000000.00, description="Gói tập 6 tháng, ưu đãi tốt")
        package_12m = GymPackage(name="Gói 12 tháng", duration_months=12, price=3500000.00, description="Gói tập 1 năm, giá tốt nhất")

        db.session.add_all([package_1m, package_3m, package_6m, package_12m])
        db.session.commit()
        print("   -> Gym Packages OK.")

        # --- BƯỚC 4B: GÓI PT (PERSONAL TRAINER PACKAGE) ---
        print("\n[Bước 4B] Seed PT Packages...")
        # PT (Personal Trainer) packages - bảng riêng
        pt_1m = PTPackage(name="Gói PT 1 tháng", duration_months=1, price=3000000.00, description="12 buổi tập 1-1 với PT chuyên nghiệp")
        pt_3m = PTPackage(name="Gói PT 3 tháng", duration_months=3, price=8000000.00, description="36 buổi tập 1-1 với PT, tiết kiệm 10%")
        pt_6m = PTPackage(name="Gói PT 6 tháng", duration_months=6, price=15000000.00, description="72 buổi tập 1-1 với PT, tiết kiệm 15%")
        pt_12m = PTPackage(name="Gói PT 12 tháng", duration_months=12, price=28000000.00, description="144 buổi tập 1-1 với PT, tiết kiệm 20%")

        db.session.add_all([pt_1m, pt_3m, pt_6m, pt_12m])
        db.session.commit()
        print("   -> PT Packages OK.")

        # --- BƯỚC 5: ĐĂNG KÝ GÓI (MEMBERSHIP) ---
        print("\n[Bước 5] Seed Memberships...")
        now = datetime.now(timezone.utc)
        
        # Member 1: Gói 12 tháng (đã đăng ký 6 tháng trước)
        start_date_1 = now - timedelta(days=180)
        end_date_1 = start_date_1 + timedelta(days=365)
        membership_1 = Membership(
            member=member_1, package=package_12m,
            start_date=start_date_1, end_date=end_date_1, active=True
        )
        
        # Member 2: Gói 3 tháng (đã đăng ký 3 tháng trước)
        start_date_2 = now - timedelta(days=90)
        end_date_2 = start_date_2 + timedelta(days=90)
        membership_2 = Membership(
            member=member_2, package=package_3m,
            start_date=start_date_2, end_date=end_date_2, active=True
        )
        
        # Member 3: Gói 6 tháng (đã đăng ký 2 tháng trước)
        start_date_3 = now - timedelta(days=60)
        end_date_3 = start_date_3 + timedelta(days=180)
        membership_3 = Membership(
            member=member_3, package=package_6m,
            start_date=start_date_3, end_date=end_date_3, active=True
        )
        
        # Member 4: Gói 1 tháng (đã đăng ký 1 tháng trước)
        start_date_4 = now - timedelta(days=30)
        end_date_4 = start_date_4 + timedelta(days=30)
        membership_4 = Membership(
            member=member_4, package=package_1m,
            start_date=start_date_4, end_date=end_date_4, active=True
        )
        
        # Member 5: Gói 3 tháng (đã đăng ký 15 ngày trước)
        start_date_5 = now - timedelta(days=15)
        end_date_5 = start_date_5 + timedelta(days=90)
        membership_5 = Membership(
            member=member_5, package=package_3m,
            start_date=start_date_5, end_date=end_date_5, active=True
        )

        db.session.add_all([
            membership_1, membership_2, membership_3, membership_4, membership_5
        ])
        db.session.commit()
        print("   -> Memberships OK.")

        # --- BƯỚC 6: THANH TOÁN ---
        print("\n[Bước 6] Seed Payments...")
        payment_1 = Payment(
            member=member_1, amount=package_12m.price,
            payment_date=start_date_1, note=f"Payment for {package_12m.name}",
            status="PAID", txn_ref="TXN001", paid_at=start_date_1
        )
        payment_2 = Payment(
            member=member_2, amount=package_3m.price,
            payment_date=start_date_2, note=f"Payment for {package_3m.name}",
            status="PAID", txn_ref="TXN002", paid_at=start_date_2
        )
        payment_3 = Payment(
            member=member_3, amount=package_6m.price,
            payment_date=start_date_3, note=f"Payment for {package_6m.name}",
            status="PAID", txn_ref="TXN003", paid_at=start_date_3
        )
        payment_4 = Payment(
            member=member_4, amount=package_1m.price,
            payment_date=start_date_4, note=f"Payment for {package_1m.name}",
            status="PAID", txn_ref="TXN004", paid_at=start_date_4
        )
        payment_5 = Payment(
            member=member_5, amount=package_3m.price,
            payment_date=start_date_5, note=f"Payment for {package_3m.name}",
            status="PAID", txn_ref="TXN005", paid_at=start_date_5
        )
        
        db.session.add_all([payment_1, payment_2, payment_3, payment_4, payment_5])
        db.session.commit()
        print("   -> Payments OK.")

        # --- BƯỚC 7: BÀI TẬP (EXERCISE) ---
        print("\n[Bước 7] Seed Exercises...")
        exercises = [
            Exercise(name="Squat", description="Compound exercise for legs and core"),
            Exercise(name="Bench Press", description="Main chest exercise"),
            Exercise(name="Deadlift", description="Full body strength exercise"),
            Exercise(name="Pull-up", description="Upper body pulling exercise"),
            Exercise(name="Push-up", description="Bodyweight chest exercise"),
            Exercise(name="Plank", description="Core strengthening exercise"),
            Exercise(name="Lunges", description="Leg exercise for quadriceps and glutes"),
            Exercise(name="Shoulder Press", description="Shoulder strength exercise"),
            Exercise(name="Bicep Curl", description="Arm bicep exercise"),
            Exercise(name="Tricep Extension", description="Arm tricep exercise"),
            Exercise(name="Leg Press", description="Machine leg exercise"),
            Exercise(name="Cable Fly", description="Chest isolation exercise"),
            Exercise(name="Yoga Pose - Warrior", description="Yoga flexibility and strength"),
            Exercise(name="Burpee", description="Full body cardio exercise"),
            Exercise(name="Mountain Climber", description="Cardio and core exercise")
        ]
        db.session.add_all(exercises)
        db.session.commit()
        exercise_squat, exercise_bench, exercise_deadlift = exercises[0], exercises[1], exercises[2]
        print(f"   -> Exercises OK ({len(exercises)} exercises).")

        # --- BƯỚC 8: PT SUBSCRIPTION (Đăng ký gói PT) ---
        print("\n[Bước 8] Seed PT Subscriptions...")
        now = datetime.now(timezone.utc)
        
        # Member 1: PT Subscription active với trainer_1 (đã có plan)
        pt_sub_start_1 = now - timedelta(days=15)
        pt_sub_end_1 = pt_sub_start_1 + timedelta(days=30)
        pt_subscription_1 = PTSubscription(
            member=member_1,
            pt_package=pt_1m,
            trainer=trainer_1,
            start_date=pt_sub_start_1,
            end_date=pt_sub_end_1,
            active=True,
            status="active",
            notes="Member muốn tập để tăng cơ"
        )
        
        # Member 2: PT Subscription pending (chưa có trainer nhận)
        pt_subscription_2 = PTSubscription(
            member=member_2,
            pt_package=pt_3m,
            trainer=None,
            start_date=None,
            end_date=None,
            active=True,
            status="pending",
            notes="Cần trainer chuyên về yoga"
        )
        
        # Member 3: PT Subscription active với trainer_2 (chưa có plan)
        pt_sub_start_3 = now - timedelta(days=5)
        pt_sub_end_3 = pt_sub_start_3 + timedelta(days=90)
        pt_subscription_3 = PTSubscription(
            member=member_3,
            pt_package=pt_3m,
            trainer=trainer_2,
            start_date=pt_sub_start_3,
            end_date=pt_sub_end_3,
            active=True,
            status="active",
            notes="Muốn tập yoga và flexibility"
        )
        
        # Member 4: PT Subscription pending
        pt_subscription_4 = PTSubscription(
            member=member_4,
            pt_package=pt_1m,
            trainer=None,
            start_date=None,
            end_date=None,
            active=True,
            status="pending",
            notes="Cần trainer cardio"
        )
        
        # Member 5: PT Subscription active với trainer_3
        pt_sub_start_5 = now - timedelta(days=2)
        pt_sub_end_5 = pt_sub_start_5 + timedelta(days=30)
        pt_subscription_5 = PTSubscription(
            member=member_5,
            pt_package=pt_1m,
            trainer=trainer_3,
            start_date=pt_sub_start_5,
            end_date=pt_sub_end_5,
            active=True,
            status="active",
            notes="Tập để giảm cân"
        )
        
        db.session.add_all([
            pt_subscription_1, pt_subscription_2, pt_subscription_3,
            pt_subscription_4, pt_subscription_5
        ])
        db.session.commit()
        print("   -> PT Subscriptions OK.")

        # --- BƯỚC 9: KẾ HOẠCH TẬP LUYỆN ---
        print("\n[Bước 9] Seed Training Plans and Details...")
        
        # Training Plan 1: Cho member_1 với trainer_1 (đã có subscription active)
        training_plan_1 = TrainingPlan(
            pt_subscription=pt_subscription_1,
            trainer=trainer_1,
            member=member_1
        )
        db.session.add(training_plan_1)
        db.session.flush()
        
        # Training Details cho plan 1
        detail_1 = TrainingDetail(
            plan=training_plan_1, exercise=exercise_squat,
            sets=4, reps=10, days_of_week="1, 3"
        )
        detail_2 = TrainingDetail(
            plan=training_plan_1, exercise=exercise_bench,
            sets=3, reps=8, days_of_week="1, 3"
        )
        detail_3 = TrainingDetail(
            plan=training_plan_1, exercise=exercise_deadlift,
            sets=3, reps=5, days_of_week="5"
        )
        detail_4 = TrainingDetail(
            plan=training_plan_1, exercise=exercises[3],  # Pull-up
            sets=3, reps=8, days_of_week="1, 3"
        )
        
        db.session.add_all([detail_1, detail_2, detail_3, detail_4])
        db.session.commit()
        print("   -> Training Plans & Details OK.")
        
        # --- BƯỚC 10: SYSTEM SETTINGS ---
        print("\n[Bước 10] Seed System Settings...")
        setting_max_days = SystemSetting(
            key="MAX_DAYS_PER_WEEK",
            value="6"
        )
        db.session.add(setting_max_days)
        db.session.commit()
        print("   -> System Settings OK.")

        print("\n--- ✅ SEED DỮ LIỆU HOÀN TẤT! ---")
        print("\n📋 Thông tin đăng nhập mẫu (password: '1'):")
        print("  👤 Admin: admin / 1")
        print("  💪 Trainer 1: trainer_pt / 1")
        print("  💪 Trainer 2: trainer_yoga / 1")
        print("  💪 Trainer 3: trainer_cardio / 1")
        print("  📞 Receptionist: receptionist / 1")
        print("  🏋️ Member 1: hoivien_a / 1")
        print("  🏋️ Member 2: hoivien_b / 1")
        print("  🏋️ Member 3: hoivien_c / 1")
        print("  🏋️ Member 4: hoivien_d / 1")
        print("  🏋️ Member 5: hoivien_e / 1")
        print("\n📊 Dữ liệu đã seed:")
        print(f"  - {len(exercises)} bài tập")
        print("  - 4 gói GYM (1, 3, 6, 12 tháng)")
        print("  - 4 gói PT (1, 3, 6, 12 tháng)")
        print("  - 5 memberships active")
        print("  - 5 payments")
        print("  - 5 PT subscriptions (2 active, 2 pending, 1 active chưa có plan)")
        print("  - 1 training plan với 4 bài tập")
        print("  - System setting: MAX_DAYS_PER_WEEK = 6")


if __name__ == '__main__':
    # THAY ĐỔI: Thay 'app_name' bằng module/instance Flask của bạn
    # Ví dụ: nếu hàm factory của bạn là create_app(), hãy dùng như dưới đây.
    app = create_app()
    seed_data(app)