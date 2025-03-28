from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask import current_app as app
from models.model import db, User, Admin, Quiz, Question, Score, Subject, Chapter, UserAnswer
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import sqlite3
from app import login_manager
from flask_login import login_user, login_required, current_user, LoginManager, logout_user
from collections import Counter
from flask import jsonify
import matplotlib.pyplot as plt
import io
import base64
import pandas as pd
from sqlalchemy.sql import func
from sqlalchemy.sql import func, cast
from sqlalchemy import Integer
from sqlalchemy import or_






# @login_manager.unauthorized_handler
# def unauthorized():
#     if "admin" in request.path:  # If accessing admin routes
#         return redirect(url_for("admin_login"))
#     return redirect(url_for("loginUser"))  # Default user login

# Ensure only admins can access admin routes
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Ensure user is authenticated and has an admin role
        if not current_user.is_authenticated or session.get("role") != "admin":
            flash("Unauthorized Access!", "danger")
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated_function

@app.before_request
def restrict_admin_routes():
    # Exclude admin login route from restrictions
    if request.endpoint == "admin_login":
        return  # Allow access to admin login page
    
    # Restrict other admin routes
    if request.endpoint and request.endpoint.startswith("admin_"):
        if not current_user.is_authenticated or session.get("role") != "admin":
            flash("Unauthorized Access!", "danger")
            return redirect(url_for("admin_login"))




@app.route("/login/admin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        admin = Admin.query.filter_by(username=username).first()

        if admin and check_password_hash(admin.password, password):
            session.clear()  # Clear session *after* successful authentication
            logout_user()    # Ensure any logged-in user is logged out

            login_user(admin, remember=True)
            session['role'] = "admin"  # Explicitly mark as admin

            flash("Login successful!", "success")
            return redirect(url_for("admin_dashboard"))

        flash("Invalid credentials, try again!", "danger")

    return render_template("loginadmin.html")




@app.route("/admin/logout")
@login_required
@admin_required
def admin_logout():
    logout_user()
    session.clear()
    session['role'] = 'guest'  # Assign 'guest' role after logout
    flash("Logged out successfully!", "success")
    return redirect(url_for("admin_login"))




@app.route("/admin/dashboard", methods=["GET"])
@login_required
@admin_required
def admin_dashboard():
    search_query = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()  # Get category filter

    print(f"Current User: {current_user}")  
    print(f"User Type: {'Admin' if isinstance(current_user, Admin) else 'User'}")  
    print(f"Search Query: {search_query}, Category: {category}")  # Debugging

    subjects, chapters, quizzes, users = [], [], [], []

    if search_query:
        if category == "subject":
            subjects = Subject.query.filter(Subject.name.ilike(f"%{search_query}%")).all()
            if subjects:
                subject_ids = [s.id for s in subjects]
                chapters = Chapter.query.filter(Chapter.subject_id.in_(subject_ids)).all()
                quizzes = Quiz.query.filter(Quiz.subject_id.in_(subject_ids)).all()

        elif category == "chapter":
            chapters = Chapter.query.filter(Chapter.name.ilike(f"%{search_query}%")).all()
            if chapters:
                chapter_ids = [c.id for c in chapters]
                quizzes = Quiz.query.filter(Quiz.chapter_id.in_(chapter_ids)).all()

        elif category == "quiz":
            quizzes = Quiz.query.filter(Quiz.title.ilike(f"%{search_query}%")).all()

        elif category == "user":
            users = User.query.filter(
                or_(User.username.ilike(f"%{search_query}%"), User.email.ilike(f"%{search_query}%"))
            ).all()

        else:  # If no specific category, search everything
            subjects = Subject.query.filter(Subject.name.ilike(f"%{search_query}%")).all()
            chapters = Chapter.query.filter(Chapter.name.ilike(f"%{search_query}%")).all()
            quizzes = Quiz.query.filter(Quiz.title.ilike(f"%{search_query}%")).all()
            users = User.query.filter(
                or_(User.username.ilike(f"%{search_query}%"), User.email.ilike(f"%{search_query}%"))
            ).all()

    else:
        # If no search, load all data
        subjects = Subject.query.all()
        chapters = Chapter.query.all()
        quizzes = Quiz.query.all()
        users = User.query.all()

    return render_template(
        "dashboard/admin_dashboard.html",
        subjects=subjects,
        chapters=chapters,
        quizzes=quizzes,
        users=users,
        search_query=search_query,
        selected_category=category
    )



# ---------------- SUBJECT ROUTES ----------------
@app.route("/admin/subjects/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_subject():
    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]
        subject = Subject(name=name, description=description)
        db.session.add(subject)
        db.session.commit()
        flash("Subject added successfully!", "success")
        return redirect(url_for("admin_dashboard"))
    return render_template("admin/add_subject.html")

@app.route("/admin/subjects/delete/<int:subject_id>")
@login_required
@admin_required
def delete_subject(subject_id):
    subject = Subject.query.get(subject_id)
    
    if subject:
        Chapter.query.filter_by(subject_id=subject_id).delete()
        db.session.delete(subject)
        db.session.commit()
        flash("Subject deleted!", "success")
    else:
        flash("Subject not found!", "danger")
    
    return redirect(url_for("admin_dashboard"))



@app.route("/admin/subjects/edit/<int:subject_id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    if request.method == "POST":
        subject.name = request.form["name"]
        subject.description = request.form["description"]
        db.session.commit()
        flash("Subject updated successfully!", "success")
        return redirect(url_for("admin_dashboard"))
    return render_template("admin/edit_subject.html", subject=subject)


# ---------------- CHAPTER ROUTES ----------------
@app.route("/admin/chapters/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_chapter():
    subjects = Subject.query.all()
    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]
        subject_id = request.form["subject_id"]
        chapter = Chapter(name=name, description=description, subject_id=subject_id)
        db.session.add(chapter)
        db.session.commit()
        flash("Chapter added successfully!", "success")
        return redirect(url_for("admin_dashboard"))
    return render_template("admin/add_chapter.html", subjects=subjects)

@app.route("/admin/chapters/delete/<int:chapter_id>")
@login_required
@admin_required
def delete_chapter(chapter_id):
    chapter = Chapter.query.get(chapter_id)
    if chapter:
        db.session.delete(chapter)
        db.session.commit()
        flash("Chapter deleted!", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/chapters/edit/<int:chapter_id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_chapter(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    subjects = Subject.query.all()
    if request.method == "POST":
        chapter.name = request.form["name"]
        chapter.description = request.form["description"]
        chapter.subject_id = request.form["subject_id"]
        db.session.commit()
        flash("Chapter updated successfully!", "success")
        return redirect(url_for("admin_dashboard"))
    return render_template("admin/edit_chapter.html", chapter=chapter, subjects=subjects)


# ---------------- QUIZ ROUTES ----------------
@app.route("/admin/quizzes/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_quiz():
    subjects = Subject.query.all()
    
    # Get the subject_id from request args if available (for re-rendering form)
    subject_id = request.args.get("subject_id", type=int)
    
    # Fetch chapters only related to the selected subject, otherwise default to empty
    chapters = Chapter.query.filter_by(subject_id=subject_id).all() if subject_id else []

    if request.method == "POST":
        title = request.form.get("title")
        subject_id = request.form.get("subject_id")
        chapter_id = request.form.get("chapter_id")
        date_of_quiz_str = request.form.get("date_of_quiz")
        time_duration = request.form.get("time_duration")
        remarks = request.form.get("remarks")

        # Convert string date to Python date object
        try:
            date_of_quiz = datetime.strptime(date_of_quiz_str, "%Y-%m-%d").date()
        except ValueError:
            flash("Invalid date format. Please use YYYY-MM-DD.", "danger")
            return redirect(url_for("add_quiz"))

        # Create new quiz entry
        quiz = Quiz(
            title=title,
            subject_id=subject_id,
            chapter_id=chapter_id,
            date_of_quiz=date_of_quiz,
            time_duration=time_duration,
            remarks=remarks,
        )
        db.session.add(quiz)
        db.session.commit()
        flash("Quiz added successfully!", "success")
        return redirect(url_for("admin_dashboard"))

    return render_template("admin/add_quiz.html", subjects=subjects, chapters=chapters, selected_subject_id=subject_id)



@app.route("/admin/quizzes/delete/<int:quiz_id>")
@login_required
@admin_required
def delete_quiz(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    if quiz:
        db.session.delete(quiz)
        db.session.commit()
        flash("Quiz deleted!", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/quizzes/edit/<int:quiz_id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    subjects = Subject.query.all()
    chapters = Chapter.query.all()
    if request.method == "POST":
        quiz.title = request.form["title"]
        quiz.subject_id = request.form["subject_id"]
        quiz.chapter_id = request.form["chapter_id"]
        quiz.date_of_quiz = datetime.strptime(request.form["date_of_quiz"], "%Y-%m-%d").date()
        quiz.time_duration = request.form["time_duration"]
        quiz.remarks = request.form["remarks"]
        db.session.commit()
        flash("Quiz updated successfully!", "success")
        return redirect(url_for("admin_dashboard"))
    return render_template("admin/edit_quiz.html", quiz=quiz, subjects=subjects, chapters=chapters)




@app.route("/admin/quiz/<int:quiz_id>/questions", methods=["GET", "POST"])
@login_required
@admin_required
def manage_questions(quiz_id):
    """Manage questions for a specific quiz."""
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz_id).all()

    if request.method == "POST":
        question_text = request.form["question_statement"]
        option1 = request.form["option1"]
        option2 = request.form["option2"]
        option3 = request.form["option3"]
        option4 = request.form["option4"]
        correct_option = int(request.form["correct_option"])

        new_question = Question(
            quiz_id=quiz_id,
            question_statement=question_text,
            option1=option1,
            option2=option2,
            option3=option3,
            option4=option4,
            correct_option=correct_option,
        )
        db.session.add(new_question)
        db.session.commit()
        flash("Question added successfully!", "success")
        return redirect(url_for("manage_questions", quiz_id=quiz_id))

    return render_template("admin/manage_questions.html", quiz=quiz, questions=questions)


@app.route("/admin/question/delete/<int:question_id>")
@login_required
@admin_required
def delete_question(question_id):
    """Delete a question from the database."""
    question = Question.query.get_or_404(question_id)

    # ✅ Delete associated user answers first
    UserAnswer.query.filter_by(question_id=question.id).delete()

    db.session.delete(question)
    db.session.commit()
    flash("Question deleted successfully!", "danger")

    return redirect(url_for("manage_questions", quiz_id=question.quiz_id))



@app.route("/admin/question/edit/<int:question_id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_question(question_id):
    """Edit an existing question."""
    question = Question.query.get_or_404(question_id)

    if request.method == "POST":
        question.question_statement = request.form["question_statement"]
        question.option1 = request.form["option1"]
        question.option2 = request.form["option2"]
        question.option3 = request.form["option3"]
        question.option4 = request.form["option4"]
        question.correct_option = int(request.form["correct_option"])

        db.session.commit()
        flash("Question updated successfully!", "info")
        return redirect(url_for("manage_questions", quiz_id=question.quiz_id))

    return render_template("admin/edit_question.html", question=question)





# ---------------- USER ROUTES ----------------
@app.route("/admin/users/delete/<int:user_id>")
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get(user_id)
    if user:
        # Manually delete associated records
        Score.query.filter_by(user_id=user_id).delete()
        UserAnswer.query.filter_by(user_id=user_id).delete()
        
        # Now delete the user
        db.session.delete(user)
        db.session.commit()
        
        flash("User deleted successfully!", "success")
    
    return redirect(url_for("admin_dashboard"))




from flask import render_template
from sqlalchemy.sql import func
from sqlalchemy import cast, Integer

@app.route("/admin/summary")
@login_required
@admin_required
def admin_summary():
    # Total counts
    total_users = db.session.query(func.count(User.id)).scalar()
    total_quizzes = db.session.query(func.count(Quiz.id)).scalar()
    total_questions = db.session.query(func.count(Question.id)).scalar()
    total_attempts = db.session.query(func.count(Score.id)).scalar()

    # 1️⃣ User Registrations Per Month (Adjust query for DB type)
    user_registrations = db.session.query(
        func.strftime('%Y-%m', User.date_created), func.count(User.id)
    ).group_by(func.strftime('%Y-%m', User.date_created)).all()

    # 2️⃣ Subject-wise Quiz Distribution
    subject_counts = db.session.query(
        Subject.name, func.count(Quiz.id)
    ).join(Quiz, Quiz.subject_id == Subject.id).group_by(Subject.name).all()

    # 3️⃣ Correct Answers Ratio Per Subject
    correct_answers_ratio = db.session.query(
    Subject.name, func.avg(cast(Score.is_correct, Integer))
    ).join(Quiz, Quiz.subject_id == Subject.id).join(Score, Score.quiz_id == Quiz.id).group_by(Subject.name).all()


    # Convert data to JSON-safe format
    user_registrations = [{"month": u[0], "count": u[1]} for u in user_registrations]
    subject_counts = [{"subject": s[0], "count": s[1]} for s in subject_counts]
    correct_answers_ratio = [{"quiz": c[0], "avg_correct": c[1]} for c in correct_answers_ratio]

    return render_template(
        "admin/admin_summary.html",
        total_users=total_users,
        total_quizzes=total_quizzes,
        total_questions=total_questions,
        total_attempts=total_attempts,
        user_registrations=user_registrations,
        subject_counts=subject_counts,
        correct_answers_ratio=correct_answers_ratio
    )
