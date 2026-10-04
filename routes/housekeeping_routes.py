from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from flask_login import login_required, current_user
from models import db, Room, HousekeepingTask

housekeeping_bp = Blueprint('housekeeping', __name__, url_prefix='/housekeeping')


def staff_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if current_user.role not in ('admin', 'staff'):
            abort(403)
        return view(*args, **kwargs)
    return wrapped


@housekeeping_bp.route('/')
@staff_required
def board():
    rooms = Room.query.order_by(Room.room_number).all()
    tasks = HousekeepingTask.query.order_by(HousekeepingTask.updated_at.desc()).all()
    return render_template('housekeeping/board.html', rooms=rooms, tasks=tasks)


@housekeeping_bp.route('/task', methods=['POST'])
@staff_required
def create_task():
    room = Room.query.get_or_404(int(request.form['room_id']))
    existing = HousekeepingTask.query.filter_by(room_id=room.id).filter(HousekeepingTask.status != 'ready').first()
    if existing:
        flash('This room already has an active housekeeping task.', 'error')
        return redirect(url_for('housekeeping.board'))
    task = HousekeepingTask(room_id=room.id, note=request.form.get('note', 'Standard room refresh'))
    db.session.add(task)
    db.session.commit()
    flash(f'Housekeeping task created for room {room.room_number}.', 'success')
    return redirect(url_for('housekeeping.board'))


@housekeeping_bp.route('/task/<int:task_id>/status', methods=['POST'])
@staff_required
def update_status(task_id):
    task = HousekeepingTask.query.get_or_404(task_id)
    status = request.form.get('status')
    if status not in ('pending', 'cleaning', 'ready'):
        flash('Invalid housekeeping status.', 'error')
        return redirect(url_for('housekeeping.board'))
    task.status = status
    if status == 'ready':
        task.room.status = 'available'
    db.session.commit()
    flash('Housekeeping status updated.', 'success')
    return redirect(url_for('housekeeping.board'))
