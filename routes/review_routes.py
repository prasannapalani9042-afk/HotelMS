from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models import db, Review, Complaint

review_bp = Blueprint("review", __name__, url_prefix="/reviews")


@review_bp.route("/")
@login_required
def list_reviews():
    reviews = Review.query.order_by(Review.created_at.desc()).all()
    complaints = Complaint.query.filter_by(guest_id=current_user.id).all()
    return render_template("reviews/reviews.html", reviews=reviews, complaints=complaints)


@review_bp.route("/add", methods=["POST"])
@login_required
def add_review():
    rating = int(request.form["rating"])
    comment = request.form.get("comment", "")
    review = Review(guest_id=current_user.id, rating=rating, comment=comment)
    db.session.add(review)
    db.session.commit()
    flash("Thanks for your feedback!", "success")
    return redirect(url_for("review.list_reviews"))


@review_bp.route("/complaint", methods=["POST"])
@login_required
def add_complaint():
    description = request.form["description"]
    complaint = Complaint(guest_id=current_user.id, description=description)
    db.session.add(complaint)
    db.session.commit()
    flash("Complaint submitted. Our team will look into it.", "success")
    return redirect(url_for("review.list_reviews"))


@review_bp.route("/complaint/<int:complaint_id>/resolve", methods=["POST"])
@login_required
def resolve_complaint(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)
    complaint.status = "resolved"
    db.session.commit()
    flash("Complaint marked resolved.", "success")
    return redirect(url_for("review.list_reviews"))
