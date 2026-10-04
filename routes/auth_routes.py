from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        # Public registration can only create safe end-user roles.
        role = request.form.get("role", "guest")
        if role not in ("guest", "student"):
            role = "guest"

        if User.query.filter_by(email=email).first():
            flash("An account with that email already exists.", "error")
            return redirect(url_for("auth.register"))

        user = User(name=name, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash("Account created! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("auth.dashboard"))
        flash("Invalid email or password.", "error")

    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))


@auth_bp.route("/dashboard")
@login_required
def dashboard():
    from datetime import date
    from models import Room, Booking, Order, Review, Complaint

    rooms = Room.query.all()
    bookings = Booking.query.order_by(Booking.created_at.desc()).all()
    active_bookings = [b for b in bookings if b.status == "confirmed"]
    today = date.today()
    today_checkins = sum(1 for b in active_bookings if b.check_in == today)
    today_checkouts = sum(1 for b in active_bookings if b.check_out == today)
    revenue = sum((b.room.price_per_night * (b.check_out - b.check_in).days) for b in bookings if b.payment_status == "paid" and b.status != "cancelled")
    food_revenue = sum(o.total_bill for o in Order.query.all() if o.status != "cancelled")
    stats = {
        "rooms": len(rooms),
        "available": sum(1 for r in rooms if r.status == "available"),
        "active_bookings": len(active_bookings),
        "today_checkins": today_checkins,
        "today_checkouts": today_checkouts,
        "revenue": revenue + food_revenue,
        "reviews": Review.query.count(),
        "complaints": Complaint.query.filter(Complaint.status != "resolved").count(),
    }
    recent_bookings = bookings[:5]
    return render_template("dashboard.html", user=current_user, stats=stats, recent_bookings=recent_bookings)
