import time
from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_required, current_user
from models import db, QuizQuestion, QuizScore

quiz_bp = Blueprint("quiz", __name__, url_prefix="/quiz")


@quiz_bp.route("/")
@login_required
def quiz_home():
    levels = sorted({q.level for q in QuizQuestion.query.all()})
    return render_template("quiz/quiz_home.html", levels=levels)


@quiz_bp.route("/play/<int:level>", methods=["GET", "POST"])
@login_required
def play(level):
    questions = QuizQuestion.query.filter_by(level=level).all()

    if request.method == "POST":
        score = 0
        for q in questions:
            selected = request.form.get(f"q{q.id}")
            if selected == q.correct_option:
                score += 10

        coins = score // 10
        time_taken = int(time.time()) - session.get("quiz_start_time", int(time.time()))

        result = QuizScore(
            user_id=current_user.id,
            level=level,
            score=score,
            coins=coins,
            time_taken_seconds=max(time_taken, 0),
        )
        db.session.add(result)
        db.session.commit()
        flash(f"Level {level} complete! You scored {score} points and earned {coins} coins.", "success")
        return redirect(url_for("quiz.leaderboard"))

    session["quiz_start_time"] = int(time.time())
    return render_template("quiz/play.html", questions=questions, level=level)


@quiz_bp.route("/leaderboard")
@login_required
def leaderboard():
    top_scores = (
        QuizScore.query.order_by(QuizScore.score.desc()).limit(10).all()
    )
    my_history = (
        QuizScore.query.filter_by(user_id=current_user.id)
        .order_by(QuizScore.completed_at.desc())
        .all()
    )
    return render_template("quiz/leaderboard.html", top_scores=top_scores, my_history=my_history)


# ---- Admin: manage questions ----
@quiz_bp.route("/admin/questions", methods=["GET", "POST"])
@login_required
def manage_questions():
    if current_user.role != "admin":
        flash("Admin access only.", "error")
        return redirect(url_for("quiz.quiz_home"))

    if request.method == "POST":
        q = QuizQuestion(
            level=int(request.form["level"]),
            question=request.form["question"],
            option_a=request.form["option_a"],
            option_b=request.form["option_b"],
            option_c=request.form["option_c"],
            option_d=request.form["option_d"],
            correct_option=request.form["correct_option"].upper(),
        )
        db.session.add(q)
        db.session.commit()
        flash("Question added.", "success")
        return redirect(url_for("quiz.manage_questions"))

    questions = QuizQuestion.query.all()
    return render_template("quiz/admin_questions.html", questions=questions)


@quiz_bp.route("/admin/questions/<int:question_id>/delete", methods=["POST"])
@login_required
def delete_question(question_id):
    if current_user.role != "admin":
        flash("Admin access only.", "error")
        return redirect(url_for("quiz.quiz_home"))
    q = QuizQuestion.query.get_or_404(question_id)
    db.session.delete(q)
    db.session.commit()
    flash("Question deleted.", "success")
    return redirect(url_for("quiz.manage_questions"))
