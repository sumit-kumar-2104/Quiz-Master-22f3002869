from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

# ===========================
# ✅ Admin Model
# ===========================
class Admin(db.Model, UserMixin):
    __tablename__ = "admin"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    full_name = db.Column(db.String, nullable=False)
    phone_number = db.Column(db.String, nullable=True)  # Optional
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    role = db.Column(db.String, nullable=False)  # Role: "student" or "admin"

    @property
    def is_admin(self):
        return True  # Always True for Admin users

    def is_authenticated(self):
        return True  # Required for Flask-Login


# ===========================
# ✅ User Model
# ===========================
class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String, unique=True, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    full_name = db.Column(db.String, nullable=False)
    qualification = db.Column(db.String, nullable=False)
    dob = db.Column(db.Date, nullable=False)
    role = db.Column(db.String, nullable=False)  # Role: "student" or "admin"
    is_active = db.Column(db.Boolean, default=True)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)

    scores = db.relationship("Score", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    answers = db.relationship("UserAnswer", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)

    def __repr__(self):
        return f"<User {self.username}>"

    def get_id(self):
        return str(self.id)

    def is_authenticated(self):
        return True  # Required for Flask-Login


# ===========================
# ✅ Subject Model
# ===========================
class Subject(db.Model):
    __tablename__ = "subjects"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, unique=True, nullable=False)
    description = db.Column(db.String)

    chapters = db.relationship("Chapter", back_populates="subject", cascade="all, delete-orphan", passive_deletes=True)
    quizzes = db.relationship("Quiz", back_populates="subject", cascade="all, delete-orphan", passive_deletes=True)


# ===========================
# ✅ Chapter Model
# ===========================
class Chapter(db.Model):
    __tablename__ = "chapters"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)

    subject = db.relationship("Subject", back_populates="chapters")
    
    # ✅ Ensure Quizzes are deleted when Chapter is deleted
    quizzes = db.relationship(
        "Quiz",
        back_populates="chapter",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

Subject.chapters = db.relationship("Chapter", order_by=Chapter.id, back_populates="subject")



# ===========================
# ✅ Quiz Model
# ===========================
class Quiz(db.Model):
    __tablename__ = "quizzes"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String, nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    chapter_id = db.Column(db.Integer, db.ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False)  # ✅ Ensure cascade delete
    date_of_quiz = db.Column(db.Date, nullable=False)
    time_duration = db.Column(db.String, nullable=False)  # Format: HH:MM
    remarks = db.Column(db.String)

    subject = db.relationship("Subject", back_populates="quizzes")
    chapter = db.relationship("Chapter", back_populates="quizzes")

    # ✅ Ensure dependent objects are deleted
    questions = db.relationship("Question", back_populates="quiz", cascade="all, delete-orphan", passive_deletes=True)
    scores = db.relationship("Score", back_populates="quiz", cascade="all, delete-orphan", passive_deletes=True)
    answers = db.relationship("UserAnswer", back_populates="quiz", cascade="all, delete-orphan", passive_deletes=True)

Subject.quizzes = db.relationship("Quiz", order_by=Quiz.id, back_populates="subject")
Chapter.quizzes = db.relationship("Quiz", order_by=Quiz.id, back_populates="chapter")


# ===========================
# ✅ Question Model
# ===========================
class Question(db.Model):
    __tablename__ = "questions"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    question_statement = db.Column(db.String, nullable=False)
    option1 = db.Column(db.String, nullable=False)
    option2 = db.Column(db.String, nullable=False)
    option3 = db.Column(db.String, nullable=False)
    option4 = db.Column(db.String, nullable=False)
    correct_option = db.Column(db.Integer, nullable=False)  # Stores 1, 2, 3, or 4

    quiz = db.relationship("Quiz", back_populates="questions")
    answers = db.relationship("UserAnswer", back_populates="question", cascade="all, delete-orphan", passive_deletes=True)

Quiz.questions = db.relationship("Question", order_by=Question.id, back_populates="quiz")


# ===========================
# ✅ Score Model
# ===========================
class Score(db.Model):
    __tablename__ = "scores"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    time_stamp_of_attempt = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    total_score = db.Column(db.Integer, nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)
    quiz = db.relationship("Quiz", back_populates="scores")  # ✅ Relationship Added
    user = db.relationship("User", back_populates="scores")  # ✅ Relationship Added

Quiz.scores = db.relationship("Score", order_by=Score.id, back_populates="quiz")
User.scores = db.relationship("Score", order_by=Score.id, back_populates="user")


# ===========================
# ✅ User Answer Model
# ===========================
class UserAnswer(db.Model):
    __tablename__ = "user_answers"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    selected_option = db.Column(db.Integer, nullable=True)  # Stores the user's selected option
    is_correct = db.Column(db.Boolean, nullable=False)

    user = db.relationship("User", back_populates="answers")
    quiz = db.relationship("Quiz", back_populates="answers")
    question = db.relationship("Question", back_populates="answers")

User.answers = db.relationship("UserAnswer", order_by=UserAnswer.id, back_populates="user")
Quiz.answers = db.relationship("UserAnswer", order_by=UserAnswer.id, back_populates="quiz")
Question.answers = db.relationship("UserAnswer", order_by=UserAnswer.id, back_populates="question")
