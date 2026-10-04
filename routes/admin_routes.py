from datetime import date
from io import BytesIO
from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, request, flash, send_file, abort
from flask_login import login_required, current_user
from models import db, Room, Booking, Order

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if current_user.role != 'admin':
            abort(403)
        return view(*args, **kwargs)
    return wrapped


@admin_bp.route('/control')
@admin_required
def control():
    rooms = Room.query.order_by(Room.room_number).all()
    bookings = Booking.query.order_by(Booking.created_at.desc()).all()
    today = date.today()
    paid_room = sum(b.room.price_per_night * max(0, (b.check_out - b.check_in).days)
                    for b in bookings if b.payment_status == 'paid' and b.status != 'cancelled')
    dining = sum(o.total_bill for o in Order.query.all() if o.status != 'cancelled')
    metrics = {
        'rooms': len(rooms),
        'ready': sum(r.status == 'available' for r in rooms),
        'maintenance': sum(r.status == 'maintenance' for r in rooms),
        'stays': sum(b.status == 'confirmed' for b in bookings),
        'today_checkins': sum(b.status == 'confirmed' and b.check_in == today for b in bookings),
        'revenue': paid_room + dining,
    }
    return render_template('admin/control.html', rooms=rooms, bookings=bookings[:8], metrics=metrics)


@admin_bp.route('/rooms/<int:room_id>/status', methods=['POST'])
@admin_required
def update_room_status(room_id):
    room = Room.query.get_or_404(room_id)
    status = request.form.get('status', '')
    if status not in ('available', 'maintenance'):
        flash('Invalid room status.', 'error')
        return redirect(url_for('admin.control'))
    room.status = status
    db.session.commit()
    flash(f'Room {room.room_number} is now {status}.', 'success')
    return redirect(url_for('admin.control'))


@admin_bp.route('/bookings/<int:booking_id>/complete', methods=['POST'])
@admin_required
def complete_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    booking.status = 'completed'
    db.session.commit()
    flash('Stay marked as completed.', 'success')
    return redirect(url_for('admin.control'))


@admin_bp.route('/invoice/<int:booking_id>')
@login_required
def invoice(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.guest_id != current_user.id and current_user.role != 'admin':
        abort(403)
    nights = max(0, (booking.check_out - booking.check_in).days)
    room_total = booking.room.price_per_night * nights
    tax = room_total * 0.12
    grand_total = room_total + tax

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.pdfgen import canvas
    except ImportError:
        flash('PDF support is not installed. Run: pip install -r requirements.txt', 'error')
        return redirect(url_for('booking.my_bookings'))

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    pdf.setFillColor(colors.HexColor('#0b1020'))
    pdf.rect(0, height - 110, width, 110, fill=1, stroke=0)
    pdf.setFillColor(colors.HexColor('#e8c978'))
    pdf.setFont('Helvetica-Bold', 24)
    pdf.drawString(45, height - 55, 'HotelMS AURA')
    pdf.setFillColor(colors.white)
    pdf.setFont('Helvetica', 10)
    pdf.drawString(45, height - 76, 'Luxury stay invoice · Guest experience platform')
    pdf.setFillColor(colors.HexColor('#111827'))
    pdf.setFont('Helvetica-Bold', 16)
    pdf.drawString(45, height - 150, f'INVOICE #{booking.id:05d}')
    pdf.setFont('Helvetica', 10)
    pdf.drawString(45, height - 170, f'Issued: {date.today().strftime("%d %b %Y")}')
    y = height - 220
    rows = [
        ('Guest', booking.guest.name), ('Email', booking.guest.email),
        ('Room', f'{booking.room.room_number} · {booking.room.room_type}'),
        ('Stay', f'{booking.check_in} → {booking.check_out} ({nights} nights)'),
        ('Payment', booking.payment_status.upper()),
    ]
    for label, value in rows:
        pdf.setFont('Helvetica-Bold', 10); pdf.drawString(55, y, label)
        pdf.setFont('Helvetica', 10); pdf.drawString(170, y, str(value)); y -= 22
    y -= 15
    pdf.line(45, y, width - 45, y); y -= 28
    pdf.setFont('Helvetica-Bold', 11); pdf.drawString(55, y, 'Room charges')
    pdf.drawRightString(width - 55, y, f'Rs. {room_total:,.2f}'); y -= 24
    pdf.setFont('Helvetica', 10); pdf.drawString(55, y, 'GST / service tax (12%)')
    pdf.drawRightString(width - 55, y, f'Rs. {tax:,.2f}'); y -= 25
    pdf.line(45, y, width - 45, y); y -= 30
    pdf.setFont('Helvetica-Bold', 14); pdf.drawString(55, y, 'TOTAL')
    pdf.drawRightString(width - 55, y, f'Rs. {grand_total:,.2f}')
    pdf.setFont('Helvetica-Oblique', 9)
    pdf.drawString(45, 45, 'Thank you for choosing HotelMS Aura.')
    pdf.save(); buffer.seek(0)
    return send_file(buffer, mimetype='application/pdf', as_attachment=True,
                     download_name=f'hotelms-invoice-{booking.id}.pdf')
