"""Run this once to populate the database with sample data:  python seed.py"""
from app import create_app
from models import db, User, Room, FoodItem, QuizQuestion, Subject

app = create_app()

with app.app_context():
    # --- Users ---
    if not User.query.filter_by(email="admin@hotel.com").first():
        admin = User(name="Admin", email="admin@hotel.com", role="admin")
        admin.set_password("admin123")
        db.session.add(admin)

    if not User.query.filter_by(email="teacher@hotel.com").first():
        teacher = User(name="Mr. Teacher", email="teacher@hotel.com", role="teacher")
        teacher.set_password("teacher123")
        db.session.add(teacher)

    if not User.query.filter_by(email="student1@hotel.com").first():
        student1 = User(name="Student One", email="student1@hotel.com", role="student")
        student1.set_password("student123")
        db.session.add(student1)

    if not User.query.filter_by(email="guest@hotel.com").first():
        guest = User(name="Guest User", email="guest@hotel.com", role="guest")
        guest.set_password("guest123")
        db.session.add(guest)

    db.session.commit()

    # --- Rooms ---
    if Room.query.count() == 0:
        rooms = [
            Room(room_number="101", room_type="Single", price_per_night=2000),
            Room(room_number="102", room_type="Double", price_per_night=3500),
            Room(room_number="201", room_type="Suite", price_per_night=7000),
        ]
        db.session.add_all(rooms)

    # --- Food items ---
    if FoodItem.query.count() == 0:
        items = [
            FoodItem(name="Masala Dosa", price=120, category="Breakfast"),
            FoodItem(name="Paneer Butter Masala", price=280, category="Main Course"),
            FoodItem(name="Veg Biryani", price=250, category="Main Course"),
            FoodItem(name="Gulab Jamun", price=90, category="Dessert"),
        ]
        db.session.add_all(items)

    # --- Quiz questions ---
    if QuizQuestion.query.count() == 0:
        questions = [
            QuizQuestion(
                level=1,
                question="What is the capital of France?",
                option_a="Berlin", option_b="Paris", option_c="Rome", option_d="Madrid",
                correct_option="B",
            ),
            QuizQuestion(
                level=1,
                question="How many continents are there?",
                option_a="5", option_b="6", option_c="7", option_d="8",
                correct_option="C",
            ),
            QuizQuestion(
                level=2,
                question="What is the largest planet in our solar system?",
                option_a="Earth", option_b="Saturn", option_c="Jupiter", option_d="Mars",
                correct_option="C",
            ),
        ]
        db.session.add_all(questions)

    # --- Subjects ---
    if Subject.query.count() == 0:
        teacher = User.query.filter_by(email="teacher@hotel.com").first()
        db.session.add(Subject(name="Housekeeping Training", teacher_id=teacher.id))

    db.session.commit()
    print("Database seeded successfully!")
    print("Login with: admin@hotel.com / admin123, teacher@hotel.com / teacher123,")
    print("student1@hotel.com / student123, guest@hotel.com / guest123")
