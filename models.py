from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


# ---------- Shared ----------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    # role: admin, staff, guest, teacher, student
    role = db.Column(db.String(20), nullable=False, default="guest")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# ---------- Module 1: Hotel Booking ----------
class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.String(10), unique=True, nullable=False)
    room_type = db.Column(db.String(50), nullable=False)  # Single, Double, Suite
    price_per_night = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default="available")  # available, booked, maintenance


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    guest_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey("room.id"), nullable=False)
    check_in = db.Column(db.Date, nullable=False)
    check_out = db.Column(db.Date, nullable=False)
    payment_status = db.Column(db.String(20), default="pending")  # pending, paid
    status = db.Column(db.String(20), default="confirmed")  # confirmed, cancelled, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    guest = db.relationship("User", backref="bookings")
    room = db.relationship("Room", backref="bookings")


# ---------- Module 2: Guest Services ----------
class FoodItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), default="Main Course")


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    guest_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey("booking.id"), nullable=True)
    items = db.Column(db.Text, nullable=False)  # "Item x qty, Item x qty"
    total_bill = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default="placed")  # placed, preparing, delivered
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    guest = db.relationship("User", backref="orders")


# ---------- Module 2B: Housekeeping ----------
class HousekeepingTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey("room.id"), nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    status = db.Column(db.String(20), default="pending")  # pending, cleaning, ready
    note = db.Column(db.String(255), default="Standard room refresh")
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    room = db.relationship("Room", backref="housekeeping_tasks")
    staff = db.relationship("User", backref="housekeeping_tasks")


# ---------- Module 3: Reviews & Feedback ----------
class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    guest_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    guest = db.relationship("User", backref="reviews")


class Complaint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    guest_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default="open")  # open, in_progress, resolved
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    guest = db.relationship("User", backref="complaints")


# ---------- Module 4: Quiz Game ----------
class QuizQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    level = db.Column(db.Integer, nullable=False, default=1)
    question = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(200), nullable=False)
    option_b = db.Column(db.String(200), nullable=False)
    option_c = db.Column(db.String(200), nullable=False)
    option_d = db.Column(db.String(200), nullable=False)
    correct_option = db.Column(db.String(1), nullable=False)  # A, B, C, D


class QuizScore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    level = db.Column(db.Integer, nullable=False)
    score = db.Column(db.Integer, default=0)
    coins = db.Column(db.Integer, default=0)
    time_taken_seconds = db.Column(db.Integer, default=0)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="quiz_scores")


# ---------- Module 5: Staff & Attendance ----------
class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    teacher = db.relationship("User", backref="subjects")


class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey("subject.id"), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(10), nullable=False, default="present")  # present, absent

    student = db.relationship("User", backref="attendance_records")
    subject = db.relationship("Subject", backref="attendance_records")

# ---------- Module 6: Advanced Guest Experience ----------
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    message = db.Column(db.String(300), nullable=False)
    kind = db.Column(db.String(30), default="info")
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship("User", backref="notifications")


class PaymentTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("booking.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    method = db.Column(db.String(30), default="demo_card")
    reference = db.Column(db.String(40), unique=True, nullable=False)
    status = db.Column(db.String(20), default="success")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    booking = db.relationship("Booking", backref="transactions")


class GuestPreference(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True, nullable=False)
    room_preference = db.Column(db.String(50), default="No preference")
    dietary = db.Column(db.String(80), default="No preference")
    special_note = db.Column(db.String(255), default="")
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user = db.relationship("User", backref=db.backref("preference", uselist=False))
