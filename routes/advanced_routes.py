from datetime import date, datetime, timedelta
from uuid import uuid4
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from models import db, Room, Booking, Order, Review, Complaint, Notification, PaymentTransaction, GuestPreference

advanced_bp = Blueprint("advanced", __name__)


def notify(user_id, title, message, kind="info"):
    db.session.add(Notification(user_id=user_id, title=title, message=message, kind=kind))


@advanced_bp.route("/guest-hub")
@login_required
def guest_hub():
    bookings = Booking.query.filter_by(guest_id=current_user.id).order_by(Booking.created_at.desc()).all()
    orders = Order.query.filter_by(guest_id=current_user.id).order_by(Order.created_at.desc()).limit(5).all()
    notes = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(8).all()
    preference = GuestPreference.query.filter_by(user_id=current_user.id).first()
    active = next((b for b in bookings if b.status == "confirmed"), None)
    return render_template("advanced/guest_hub.html", bookings=bookings, orders=orders, notes=notes, preference=preference, active=active)


@advanced_bp.route("/preferences", methods=["POST"])
@login_required
def preferences():
    pref = GuestPreference.query.filter_by(user_id=current_user.id).first()
    if not pref:
        pref = GuestPreference(user_id=current_user.id)
        db.session.add(pref)
    pref.room_preference = request.form.get("room_preference", "No preference")[:50]
    pref.dietary = request.form.get("dietary", "No preference")[:80]
    pref.special_note = request.form.get("special_note", "")[:255]
    db.session.commit()
    flash("Guest preferences saved to your profile.", "success")
    return redirect(url_for("advanced.guest_hub"))


@advanced_bp.route("/notifications/<int:notification_id>/read", methods=["POST"])
@login_required
def read_notification(notification_id):
    note = Notification.query.get_or_404(notification_id)
    if note.user_id != current_user.id:
        abort(403)
    note.is_read = True
    db.session.commit()
    return redirect(request.referrer or url_for("advanced.guest_hub"))


@advanced_bp.route("/concierge", methods=["GET", "POST"])
@login_required
def concierge():
    answer = None
    if request.method == "POST":
        q = request.form.get("question", "").strip().lower()
        if any(x in q for x in ["room", "suite", "stay"]):
            answer = "For a premium stay, check Stays & Rooms. Suite rooms are best for longer stays and special occasions."
        elif any(x in q for x in ["food", "dinner", "breakfast", "restaurant"]):
            answer = "Dining & Service lets you order from the hotel menu. Your order status can be tracked from My Orders."
        elif any(x in q for x in ["invoice", "bill", "receipt"]):
            answer = "Open your reservation in My Bookings and use Download Invoice. Your room charges and GST are calculated automatically."
        elif any(x in q for x in ["check in", "check-in", "arrival"]):
            answer = "Your confirmed reservation contains the arrival date. For a faster arrival, keep your booking details ready at reception."
        elif any(x in q for x in ["cancel", "cancellation"]):
            answer = "You can cancel an active reservation from My Bookings. Cancelled stays no longer count as active reservations."
        else:
            answer = "I can help with rooms, stays, dining, invoices, check-in and cancellations. Try asking one of those."
    return render_template("advanced/concierge.html", answer=answer)


@advanced_bp.route("/demo-pay/<int:booking_id>", methods=["POST"])
@login_required
def demo_pay(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.guest_id != current_user.id and current_user.role != "admin":
        abort(403)
    if booking.status != "confirmed":
        flash("Only active bookings can be paid.", "error")
        return redirect(url_for("booking.my_bookings"))
    nights = max(1, (booking.check_out - booking.check_in).days)
    amount = booking.room.price_per_night * nights * 1.12
    if not PaymentTransaction.query.filter_by(booking_id=booking.id, status="success").first():
        tx = PaymentTransaction(booking_id=booking.id, amount=amount, method="demo_card", reference="AURA-" + uuid4().hex[:10].upper())
        db.session.add(tx)
    booking.payment_status = "paid"
    notify(booking.guest_id, "Payment confirmed", f"Reservation #{booking.id:05d} is marked paid. Your digital receipt is ready.", "success")
    db.session.commit()
    flash("Demo payment successful — transaction recorded.", "success")
    return redirect(url_for("advanced.guest_hub"))


@advanced_bp.route("/analytics")
@login_required
def analytics():
    if current_user.role != "admin":
        abort(403)
    rooms = Room.query.all()
    bookings = Booking.query.all()
    orders = Order.query.all()
    total_room_revenue = sum(b.room.price_per_night * max(0, (b.check_out - b.check_in).days) for b in bookings if b.payment_status == "paid" and b.status != "cancelled")
    food_revenue = sum(o.total_bill for o in orders if o.status != "cancelled")
    total_capacity = max(1, len(rooms) * 30)
    sold_nights = sum(max(0, (b.check_out - b.check_in).days) for b in bookings if b.status != "cancelled")
    occupancy = min(100, round((sold_nights / total_capacity) * 100))
    room_types = {}
    for room in rooms:
        room_types[room.room_type] = room_types.get(room.room_type, 0) + 1
    top_rooms = sorted(room_types.items(), key=lambda x: x[1], reverse=True)
    recent = sorted(bookings, key=lambda b: b.created_at or datetime.min, reverse=True)[:8]
    return render_template("advanced/analytics.html", rooms=rooms, bookings=bookings, total_room_revenue=total_room_revenue, food_revenue=food_revenue, occupancy=occupancy, top_rooms=top_rooms, recent=recent)


@advanced_bp.route("/checkin/<int:booking_id>")
@login_required
def digital_checkin(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.guest_id != current_user.id and current_user.role != "admin":
        abort(403)
    if booking.status != "confirmed":
        flash("Only active reservations can be checked in.", "error")
        return redirect(url_for("booking.my_bookings"))
    return render_template("advanced/checkin.html", booking=booking, token=f"AURA-{booking.id:05d}-{booking.guest_id:04d}")
