from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models import db, User, Subject, Attendance

attendance_bp = Blueprint("attendance", __name__, url_prefix="/attendance")


@attendance_bp.route("/mark", methods=["GET", "POST"])
@login_required
def mark_attendance():
    if current_user.role not in ("teacher", "admin"):
        flash("Only teachers/admins can mark attendance.", "error")
        return redirect(url_for("auth.dashboard"))

    subjects = Subject.query.all()
    students = User.query.filter_by(role="student").all()

    if request.method == "POST":
        subject_id = int(request.form["subject_id"])
        date_str = request.form["date"]
        date = datetime.strptime(date_str, "%Y-%m-%d").date()

        for student in students:
            status = request.form.get(f"status_{student.id}", "absent")
            existing = Attendance.query.filter_by(
                student_id=student.id, subject_id=subject_id, date=date
            ).first()
            if existing:
                existing.status = status
            else:
                record = Attendance(
                    student_id=student.id, subject_id=subject_id, date=date, status=status
                )
                db.session.add(record)
        db.session.commit()
        flash("Attendance saved.", "success")
        return redirect(url_for("attendance.mark_attendance"))

    return render_template("attendance/mark_attendance.html", subjects=subjects, students=students)


@attendance_bp.route("/subjects", methods=["GET", "POST"])
@login_required
def manage_subjects():
    if current_user.role != "admin":
        flash("Admin access only.", "error")
        return redirect(url_for("auth.dashboard"))

    teachers = User.query.filter_by(role="teacher").all()

    if request.method == "POST":
        subject = Subject(name=request.form["name"], teacher_id=request.form.get("teacher_id") or None)
        db.session.add(subject)
        db.session.commit()
        flash("Subject added.", "success")
        return redirect(url_for("attendance.manage_subjects"))

    subjects = Subject.query.all()
    return render_template("attendance/manage_subjects.html", subjects=subjects, teachers=teachers)


@attendance_bp.route("/my-attendance")
@login_required
def my_attendance():
    if current_user.role != "student":
        flash("Student view only.", "error")
        return redirect(url_for("auth.dashboard"))

    records = Attendance.query.filter_by(student_id=current_user.id).order_by(Attendance.date.desc()).all()
    total = len(records)
    present = len([r for r in records if r.status == "present"])
    percentage = round((present / total) * 100, 1) if total else 0

    return render_template(
        "attendance/my_attendance.html", records=records, percentage=percentage, total=total, present=present
    )


@attendance_bp.route("/reports")
@login_required
def reports():
    if current_user.role not in ("teacher", "admin"):
        flash("Not authorized.", "error")
        return redirect(url_for("auth.dashboard"))

    students = User.query.filter_by(role="student").all()
    report_data = []
    for student in students:
        records = Attendance.query.filter_by(student_id=student.id).all()
        total = len(records)
        present = len([r for r in records if r.status == "present"])
        percentage = round((present / total) * 100, 1) if total else 0
        report_data.append({"student": student, "total": total, "present": present, "percentage": percentage})

    return render_template("attendance/reports.html", report_data=report_data)
