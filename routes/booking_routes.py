from datetime import datetime, date
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models import db, Room, Booking

booking_bp = Blueprint("booking", __name__, url_prefix="/booking")

def has_overlap(room_id, check_in, check_out, ignore_booking_id=None):
    query = Booking.query.filter(
        Booking.room_id == room_id,
        Booking.status == "confirmed",
        Booking.check_in < check_out,
        Booking.check_out > check_in,
    )
    if ignore_booking_id:
        query = query.filter(Booking.id != ignore_booking_id)
    return query.first() is not None

@booking_bp.route("/rooms")
@login_required
def rooms():
    all_rooms = Room.query.order_by(Room.room_number).all()
    available_ids = {r.id for r in all_rooms if r.status == "available"}
    check_in_raw = request.args.get("check_in", "")
    check_out_raw = request.args.get("check_out", "")
    if check_in_raw and check_out_raw:
        try:
            ci = datetime.strptime(check_in_raw, "%Y-%m-%d").date()
            co = datetime.strptime(check_out_raw, "%Y-%m-%d").date()
            if co > ci:
                available_ids = {r.id for r in all_rooms if r.status == "available" and not has_overlap(r.id, ci, co)}
        except ValueError:
            pass
    return render_template("booking/rooms.html", rooms=all_rooms, available_ids=available_ids, check_in=check_in_raw, check_out=check_out_raw)

@booking_bp.route("/book/<int:room_id>", methods=["GET", "POST"])
@login_required
def book_room(room_id):
    room = Room.query.get_or_404(room_id)
    if room.status == "maintenance":
        flash("This room is currently under maintenance.", "error")
        return redirect(url_for("booking.rooms"))

    if request.method == "POST":
        try:
            check_in = datetime.strptime(request.form["check_in"], "%Y-%m-%d").date()
            check_out = datetime.strptime(request.form["check_out"], "%Y-%m-%d").date()
        except (KeyError, ValueError):
            flash("Please enter valid booking dates.", "error")
            return redirect(url_for("booking.book_room", room_id=room.id))

        if check_in < date.today():
            flash("Check-in date cannot be in the past.", "error")
            return redirect(url_for("booking.book_room", room_id=room.id))
        if check_out <= check_in:
            flash("Check-out date must be after check-in date.", "error")
            return redirect(url_for("booking.book_room", room_id=room.id))
        if has_overlap(room.id, check_in, check_out):
            flash("Sorry, this room is already reserved for those dates.", "error")
            return redirect(url_for("booking.rooms"))

        booking = Booking(guest_id=current_user.id, room_id=room.id, check_in=check_in, check_out=check_out)
        db.session.add(booking)
        db.session.commit()
        try:
            from routes.advanced_routes import notify
            notify(current_user.id, "Reservation confirmed", f"Room {room.room_number} is reserved from {check_in} to {check_out}.", "success")
            db.session.commit()
        except Exception:
            db.session.rollback()
        flash("✨ Your stay is confirmed!", "success")
        return redirect(url_for("booking.my_bookings"))

    return render_template("booking/book_room.html", room=room, today=date.today().isoformat())

@booking_bp.route("/my-bookings")
@login_required
def my_bookings():
    bookings = Booking.query.filter_by(guest_id=current_user.id).order_by(Booking.created_at.desc()).all()
    return render_template("booking/my_bookings.html", bookings=bookings)

@booking_bp.route("/cancel/<int:booking_id>", methods=["POST"])
@login_required
def cancel_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.guest_id != current_user.id and current_user.role != "admin":
        flash("Not authorized.", "error")
        return redirect(url_for("booking.my_bookings"))
    booking.status = "cancelled"
    db.session.commit()
    flash("Booking cancelled successfully.", "success")
    return redirect(url_for("booking.my_bookings"))

@booking_bp.route("/pay/<int:booking_id>", methods=["POST"])
@login_required
def pay_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.guest_id != current_user.id and current_user.role != "admin":
        flash("Not authorized.", "error")
        return redirect(url_for("booking.my_bookings"))
    if booking.status != "confirmed":
        flash("Only active bookings can be paid.", "error")
        return redirect(url_for("booking.my_bookings"))
    booking.payment_status = "paid"
    db.session.commit()
    flash("Payment recorded successfully.", "success")
    return redirect(url_for("booking.my_bookings"))
