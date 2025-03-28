import re
from flask import Blueprint, Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask import current_app as app
from models.model import db, User, Admin, Quiz, Question, Score, Subject, Chapter,  UserAnswer
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import sqlite3
from flask_login import login_user, login_required, current_user, LoginManager, logout_user
from flask import request, session, redirect, url_for, render_template, flash
from flask_login import login_user, login_required, current_user, logout_user
import secrets

user_bp = Blueprint("user", __name__)


from flask import request, session, redirect, url_for, render_template, flash
from flask_login import logout_user, login_required, current_user
import secrets




@app.before_request
def restrict_user_routes():
    # Allow access to login and other public routes
    if request.endpoint in ["user.loginUser", "admin_login"]:
        return

    # Restrict access to user-specific routes
    if request.endpoint and request.endpoint.startswith("user_"):
        if not current_user.is_authenticated or session.get("role") != "user":
            flash("Unauthorized Access!", "danger")
            return redirect(url_for("user.loginUser"))



def get_db_connection():
    conn = sqlite3.connect("database/quiz_master.sqlite3")
    conn.row_factory = sqlite3.Row
    return conn



# User Login Route
# User Login Route
@user_bp.route('/login/user', methods=['GET', 'POST'])
def loginUser():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            if user.role == "admin":
                flash("Admins must log in via the admin portal!", "danger")
                return redirect(url_for("admin_login"))  # Prevent admin access via user login

            session.clear()  # Clear session *after* authentication
            logout_user()  # Ensure any logged-in user is logged out
            # session['csrf_token'] = secrets.token_hex(16)  # Regenerate CSRF token

            login_user(user, remember=True)
            session['user_id'] = user.id
            session['role'] = "user"  # Explicitly store role

            flash('Login successful!', 'success')
            return redirect(url_for("user.user_dashboard"))

        flash('Invalid username or password!', 'danger')

    return render_template('loginuser.html')



# User Logout Route
@user_bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    session['role'] = 'guest'  # Assign 'guest' role after logout
    session.modified = True
    flash('You have been logged out.', 'info')
    return redirect(url_for('user.loginUser'))



# Helper function to set session variables after successful login
def logInUser(user, usertype):
    session.update({
        "loggedin": True,
        "usertype": usertype,
        "user_id": user.id,
        "username": user.username
    })


@property
def is_active(self):
    # You can add custom logic here — like checking if the account is banned or something
    return True


# Helper function to handle login process
def handle_login(model, usertype, dashboard):
    username = request.form['username']
    password = request.form['password']

    user = model.query.filter_by(username=username).first()

    if user and check_password_hash(user.password, password):
        # Role-based login restriction
        if usertype == "user" and hasattr(user, "role") and user.role == "admin":
            flash("Admins must log in from the admin portal!", "warning")
            return redirect(url_for("admin.loginAdmin"))  # Redirect to admin login

        if usertype == "admin" and hasattr(user, "role") and user.role != "admin":
            flash("Only admins can access this login!", "warning")
            return redirect(url_for("user.loginUser"))  # Redirect to user login

        login_user(user, remember=True)  # <-- Proper login method
        flash('Login successful!', 'success')
        return redirect(url_for(dashboard))
    
    elif user:
        flash('Invalid password', 'danger')
    else:
        flash('Username not registered', 'warning')
        return redirect(url_for(f'user.register{usertype}'))
    
    return render_template(f'login{usertype}.html')


# User registration route
@user_bp.route('/register/user', methods=['GET', 'POST'], endpoint='registeruser')
def registerUser():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        full_name = request.form['full_name']
        qualification = request.form['qualification']
        dob = datetime.strptime(request.form['dob'], "%Y-%m-%d").date()
        role = "user"
        date_created = datetime.utcnow()

        # Email format validation
        email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_regex, email):
            flash('Invalid email format! Please enter a valid email.', 'danger')
            return render_template('user/registeruser.html')

        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already taken. Please choose a different one.', 'danger')
            return render_template('user/registeruser.html')

        if User.query.filter_by(email=email).first():
            flash('Email already in use. Try another.', 'danger')
            return render_template('user/registeruser.html')

        # Hash the password before storing it
        hashed_password = generate_password_hash(password)

        new_user = User(username=username, password=hashed_password, email=email,
                        full_name=full_name, qualification=qualification, dob=dob,
                        role=role, date_created=date_created)

        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! You can now login.', 'success')
        return redirect(url_for('user.loginUser'))

    return render_template('user/registeruser.html')



# User Dashboard Route
@user_bp.route('/user_dashboard')
@login_required
def user_dashboard():
    user = current_user

    # For debugging, print or log the current user's role
    app.logger.debug("Current user role: %s", current_user.role)

    if session.get('role') != "user":
        flash("Unauthorized Access!", "danger")
        return redirect(url_for('user.loginUser'))

    # Ensure only users access the user dashboard
    if current_user.role != "user":
        flash("Unauthorized access! Redirecting...", "danger")
        return redirect(url_for("admin_dashboard"))
    
    if not current_user.is_authenticated:
        return redirect(url_for('user.loginUser'))

    conn = get_db_connection()

    # Fetch subjects
    subjects = db.session.query(Subject.id, Subject.name).distinct().all()

    # Fetch Upcoming Quizzes
    upcoming_quizzes = (
        db.session.query(
            Quiz.id, 
            Quiz.title,  # Include Quiz Title
            Chapter.name.label("chapter_name"), 
            Quiz.date_of_quiz, 
            Quiz.time_duration, 
            Quiz.remarks
        )
        .join(Chapter)
        .filter(Quiz.date_of_quiz >= date.today())
        .order_by(Quiz.date_of_quiz.asc())
        .all()
    )


    # Fetch Quiz Scores
    quiz_scores = (
        db.session.query(
            Score.quiz_id,
            Score.time_stamp_of_attempt.label("time_stamp_of_attempt"),
            Score.total_score,
            db.case(
                (db.func.count(Question.id) > 0, (Score.total_score * 100.0 / db.func.count(Question.id))),
                else_=0
            ).label("percentage_score")
        )
        .join(Quiz, Score.quiz_id == Quiz.id)
        .outerjoin(Question, Question.quiz_id == Quiz.id)
        .filter(Score.user_id == current_user.id)
        .group_by(Score.id, Score.total_score, Score.time_stamp_of_attempt)
        .all()
    )

    conn.close()

    return render_template(
        "dashboard/user_dashboard.html",
        user=current_user,
        subjects=[{"id": s.id, "name": s.name} for s in subjects],
        upcoming_quizzes=[
            {
                "id": q.id,
                "title": q.title,  # Include Quiz Title
                "chapter_name": q.chapter_name,
                "date_of_quiz": q.date_of_quiz.strftime("%Y-%m-%d"),
                "time_duration": q.time_duration,
                "remarks": q.remarks
            } 
            for q in upcoming_quizzes
        ],
        quiz_scores=[
            {
                "quiz_id": score.quiz_id,
                "date": score.time_stamp_of_attempt.strftime("%Y-%m-%d %H:%M:%S") if score.time_stamp_of_attempt else "N/A",
                "total_score": round(float(score.percentage_score), 2) if score.percentage_score is not None else "Not Attempted"
            } 
            for score in quiz_scores
        ]
    )



# Search bar functionality
@user_bp.route("/search", methods=["GET"])
@login_required
def search():
    query = request.args.get("q", "").strip()
    results = {"subjects": [], "chapters": [], "quizzes": []}  # ✅ "quizzes" instead of "quiz"

    if query:
        results["subjects"] = Subject.query.filter(Subject.name.ilike(f"%{query}%")).all()
        results["chapters"] = Chapter.query.filter(Chapter.name.ilike(f"%{query}%")).all()
        results["quizzes"] = Quiz.query.filter(Quiz.title.ilike(f"%{query}%")).all()  # ✅ Query by `Quiz.title`

    return jsonify({
        "subjects": [{"id": s.id, "name": s.name} for s in results["subjects"]],
        "chapters": [{"id": c.id, "name": c.name} for c in results["chapters"]],
        "quizzes": [{"id": q.id, "title": q.title} for q in results["quizzes"]]  # ✅ Use `title` for quizzes
    })








@user_bp.route("/get_subjects")
@login_required
def get_subjects():
    conn = get_db_connection()
    subjects = conn.execute("SELECT id, name FROM subjects").fetchall()
    conn.close()
    return jsonify({"subjects": [{"id": s["id"], "name": s["name"]} for s in subjects]})

@user_bp.route("/get_quizzes")
@login_required
def get_quizzes():
    conn = get_db_connection()
    quizzes = conn.execute("SELECT id, title, chapter_id, date_of_quiz, time_duration, remarks FROM quizzes").fetchall()
    conn.close()
    return jsonify({
        "quizzes": [
            {
                "id": q["id"],
                "title": q["title"],  # Include Title
                "chapter_id": q["chapter_id"],
                "date_of_quiz": q["date_of_quiz"],
                "time_duration": q["time_duration"],
                "remarks": q["remarks"]
            }
            for q in quizzes
        ]
    })



@user_bp.route("/quizzes/<int:chapter_id>")
@login_required
def quizzes_by_chapter(chapter_id):
    conn = get_db_connection()
    quizzes = conn.execute(
        "SELECT id, title, date_of_quiz, time_duration, remarks FROM quizzes WHERE chapter_id = ?", 
        (chapter_id,)
    ).fetchall()
    conn.close()
    return render_template("user/quizzes.html", quizzes=quizzes)



@user_bp.route("/get_chapters/<int:subject_id>")
@login_required
def get_chapters(subject_id):
    conn = get_db_connection()
    chapters = conn.execute(
        "SELECT id, name FROM chapters WHERE subject_id = ? ORDER BY id LIMIT 5",
        (subject_id,)
    ).fetchall()
    conn.close()

    return jsonify({
        "chapters": [{"id": c["id"], "name": c["name"]} for c in chapters]
    })


@user_bp.route("/chapter/<int:chapter_id>")
@login_required
def chapter_view(chapter_id):
    conn = get_db_connection()

    # Fetch chapter details
    chapter = conn.execute("SELECT id, name FROM chapters WHERE id = ?", (chapter_id,)).fetchone()

    # Fetch quizzes related to this chapter (include title)
    quizzes = conn.execute(
        "SELECT id, title, date_of_quiz, time_duration, remarks FROM quizzes WHERE chapter_id = ?",
        (chapter_id,)
    ).fetchall()
    conn.close()

    if not chapter:
        flash("Chapter not found!", "danger")
        return redirect(url_for("user.user_dashboard"))

    return render_template("user/chapter_view.html", chapter=chapter, quizzes=quizzes)


@user_bp.route('/start_quiz/<int:quiz_id>')
@login_required
def start_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    
    return render_template("user/start_quiz.html", quiz=quiz, questions=questions, user=current_user)


@user_bp.route('/submit_quiz/<int:quiz_id>', methods=['POST'])
@login_required
def submit_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz_id).all()

    # Check if quiz has timed out
    quiz_duration = quiz.time_duration  # Assuming this is stored in minutes
    quiz_start_time = session.get(f"quiz_{quiz_id}_start_time")
    
    if quiz_start_time:
        elapsed_time = (datetime.utcnow() - quiz_start_time).total_seconds() / 60
        if elapsed_time > quiz_duration:
            flash("Time's up! Your quiz was not submitted in time.", "danger")
            return redirect("http://192.168.1.35:8080/chapter/1")

    correct_answers = 0
    total_questions = len(questions)
    user_answers = {}

    for question in questions:
        user_response = request.form.get(f"q{question.id}")
        user_answers[str(question.id)] = user_response

        is_correct = user_response and int(user_response) == question.correct_option

        # ✅ Prevent NULL values by defaulting to False
        user_answer = UserAnswer(
            user_id=current_user.id,
            quiz_id=quiz_id,
            question_id=question.id,
            selected_option=int(user_response) if user_response else None,
            is_correct=is_correct if user_response else False  # Default False if unanswered
        )
        db.session.add(user_answer)

        if is_correct:
            correct_answers += 1  

    # ✅ Save only ONE quiz-level entry in Score
    new_score = Score(
        user_id=current_user.id,
        quiz_id=quiz_id,
        total_score=correct_answers, 
        time_stamp_of_attempt=datetime.utcnow(),
        is_correct=(correct_answers > 0)
    )

    db.session.add(new_score)
    db.session.commit()  # ✅ Commit everything together

    previous_page_url = request.referrer or url_for('dashboard')

    correct_answers_dict = {q.id: q.correct_option for q in questions}

    return render_template(
        "user/quiz_result.html",
        quiz=quiz,
        questions=questions,
        user_answers=user_answers,
        correct_answers=correct_answers_dict,
        score=correct_answers,
        total_questions=total_questions,
        previous_page_url=previous_page_url,
        user=current_user
    )

@user_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    old_password = request.form['old_password']
    new_password = request.form['new_password']
    confirm_password = request.form['confirm_password']

    # Validate old password
    if not check_password_hash(current_user.password, old_password):
        flash("Old password is incorrect!", "danger")
        return redirect(url_for('user.profile'))

    # Validate new password strength
    import re
    password_regex = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
    if not re.match(password_regex, new_password):
        flash("Password must be at least 8 characters long, include upper/lower case letters, a number, and a special character.", "warning")
        return redirect(url_for('user.profile'))

    # Check if passwords match
    if new_password != confirm_password:
        flash("New passwords do not match!", "danger")
        return redirect(url_for('user.profile'))

    # Update password in database
    current_user.password = generate_password_hash(new_password)
    db.session.commit()
    flash("Password changed successfully!", "success")
    return redirect(url_for('user.profile'))

@user_bp.route('/quiz_result/<int:quiz_id>')
@login_required
def quiz_result(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    score = Score.query.filter_by(quiz_id=quiz_id, user_id=current_user.id).order_by(Score.time_stamp_of_attempt.desc()).first()
    
    if not score:
        flash("No result found!", "warning")
        return redirect(url_for('user.user_dashboard'))

    return render_template("quiz_result.html", quiz=quiz, score=score, user=current_user)



# Profile Page
@user_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user = User.query.get(current_user.id)

    if request.method == "POST":
        old_password = request.form["old_password"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        if not check_password_hash(user.password, old_password):
            flash("Old password is incorrect.", "danger")
            return redirect(url_for("user.profile"))

        if new_password != confirm_password:
            flash("New passwords do not match.", "danger")
            return redirect(url_for("user.profile"))

        user.password = generate_password_hash(new_password)
        db.session.commit()

        flash("Password updated successfully!", "success")
        return redirect(url_for("user.profile"))

    # Fetch all quizzes attempted by user
    attempted_quizzes = Quiz.query.join(Score).filter(Score.user_id == user.id).all()

    # Extract unique subjects from attempted quizzes
    subjects = list(set(quiz.chapter.subject.name for quiz in attempted_quizzes))

    # Count quizzes attempted per subject
    quizzes_attempted = [
        Quiz.query.join(Score).join(Chapter).join(Subject)
        .filter(Score.user_id == user.id, Subject.name == subject)
        .count()
        for subject in subjects
    ]

    # Compute total questions & correct answers
    total_scores = Score.query.filter_by(user_id=user.id).all()
    total_questions = sum(score.total_score for score in total_scores)
    correct_answers = sum(score.total_score for score in total_scores)  # Assuming `total_score` stores correct answers

    # ✅ Debugging Print Statements (Remove Later)
    print("Subjects:", subjects)
    print("Quizzes Attempted:", quizzes_attempted)
    print("Total Questions:", total_questions)
    print("Correct Answers:", correct_answers)

    return render_template(
        "user/profile.html",
        user=user,
        subjects=subjects,
        quizzes_attempted=quizzes_attempted,
        total_questions=total_questions,
        correct_answers=correct_answers
    )

@user_bp.route("/get_summary_data")
@login_required
def get_summary_data():
    user_id = current_user.id  # Ensure user is authenticated

    # Get all subjects
    subjects = Subject.query.all()
    subject_names = [subject.name for subject in subjects]

    # Count total quiz attempts per subject
    quizzes_attempted = [
        Score.query.join(Quiz, Quiz.id == Score.quiz_id)
        .filter(Quiz.subject_id == subject.id, Score.user_id == user_id)
        .count()
        for subject in subjects
    ]

    # Count correct answers (sum of total_score from Score table)
    correct_answers = db.session.query(db.func.sum(Score.total_score)).filter(Score.user_id == user_id).scalar() or 0

    # Calculate total attempted questions by counting questions linked to quizzes the user attempted
    total_questions_attempted = db.session.query(db.func.count(Question.id))\
        .join(Quiz, Quiz.id == Question.quiz_id)\
        .join(Score, Score.quiz_id == Quiz.id)\
        .filter(Score.user_id == user_id)\
        .scalar() or 0

    # Calculate incorrect answers
    incorrect_answers = max(0, total_questions_attempted - correct_answers)

    # Debugging output
    print("🔍 Debug Data:", {
        "subjects": subject_names,
        "quizzes_attempted": quizzes_attempted,
        "total_questions_attempted": total_questions_attempted,
        "correct_answers": correct_answers,
        "incorrect_answers": incorrect_answers
    })

    return jsonify({
        "subjects": subject_names,
        "quizzes_attempted": quizzes_attempted,
        "total_questions_attempted": total_questions_attempted,
        "correct_answers": correct_answers,
        "incorrect_answers": incorrect_answers
    })




@user_bp.route("/user/subject/<int:subject_id>")
@login_required
def subject_view(subject_id):
    conn = get_db_connection()

    # Fetch subject details
    subject = conn.execute("SELECT id, name FROM subjects WHERE id = ?", (subject_id,)).fetchone()

    if not subject:
        flash("Subject not found!", "danger")
        return redirect(url_for("user.user_dashboard"))

    # Fetch all chapters under this subject
    chapters = conn.execute("SELECT id, name FROM chapters WHERE subject_id = ?", (subject_id,)).fetchall()
    conn.close()

    return render_template("user/subject_view.html", user=current_user, subject=subject, chapters=chapters)



@user_bp.route("/profile/update", methods=["POST"])
@login_required
def update_profile():
    full_name = request.form.get("full_name")
    dob = request.form.get("dob")
    qualification = request.form.get("qualification")

    # Allowed qualification choices
    allowed_qualifications = {"Primary", "Higher", "Bachelors"}

    if qualification not in allowed_qualifications:
        flash("Invalid qualification selected!", "danger")
        return redirect(url_for("user.profile"))

    try:
        # Update user details
        current_user.full_name = full_name
        current_user.dob = datetime.strptime(dob, "%Y-%m-%d").date()
        current_user.qualification = qualification

        db.session.commit()
        flash("Profile updated successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash("Error updating profile. Please try again.", "danger")

    return redirect(url_for("user.profile"))