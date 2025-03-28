from flask import Flask, render_template, redirect, url_for, request
from datetime import datetime
from application.config import LocalDevelopmentConfig
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app
from models.model import db, Admin, User, Subject, Chapter, Quiz, Question,  UserAnswer
from sqlalchemy import text
from flask_login import LoginManager
import sqlite3


app = None
# login_manager = None  # Declare login_manager globally

# Initialize Flask-Login
login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    """Load a user based on their ID, checking both Admin and User tables."""
    admin = Admin.query.get(int(user_id))
    if admin:
        return admin  # ✅ If it's an admin, return admin

    return User.query.get(int(user_id))  # ✅ Otherwise, return user


def enable_foreign_keys(db_uri):
    """Ensure foreign key constraints are enabled in SQLite."""
    if "sqlite" in db_uri:
        with sqlite3.connect(db_uri.replace("sqlite:///", "")) as conn:
            conn.execute("PRAGMA foreign_keys=ON;")


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__, template_folder="templates")
    app.config.from_object(LocalDevelopmentConfig)
    app.secret_key = "your_super_secret_key"  # ✅ Required for Flask-Login sessions
    print("App created with configuration")
    app.app_context().push()

    from models.model import db

    # Initialize the database
    db.init_app(app)
    print(f"Database instance: {db}")

    # Enable Foreign Key Support for SQLite
    with app.app_context():
        enable_foreign_keys(app.config["SQLALCHEMY_DATABASE_URI"])  # ✅ Force enable foreign keys
        db.create_all()

        # Test DB connection (if function exists)
        test_db_connection(app)

        # Create initial data (if function exists)
        create_initial_data()


    # Set up Flask-Login after app creation
    login_manager.init_app(app)  # Initialize Flask-Login once
    login_manager.login_view = "loginUser"  # Default: User login page
    login_manager.login_message = "Please log in to access this page."


    # Test DB connection
    # test_db_connection(app)

    # create_initial_data()
    
    return app



def test_db_connection(app):
    """Test the database connection."""
    with app.app_context():
        try:
            # Execute a simple query to test the connection
            db.session.execute(text('SELECT 1'))
            print("Database connection successful!")
        except Exception as e:
            print(f"Database connection failed: {e}")



def create_initial_data():
    """Create initial data for the application."""
    
    db.create_all()

    print(f"Current app context: {current_app}")
    # Create the admin user if it doesn't exist
    # admin = User.query.filter_by(username='admin').first()
    admin = Admin.query.filter_by(username='admin').first()
    if not admin:
        admin = Admin(
            username='admin',
            password=generate_password_hash('admin'),  # Hash the password
            email='admin@example.com',
            full_name='System Administrator',
            phone_number='1234567890',
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
    
    # Check and create a separate user
    user = User.query.filter_by(username='test_user').first()
    if not user:
        user = User(
            username='test_user',
            email='test_user@example.com',
            password='test123',  # Ideally, hash this password
            full_name='Test User',
            qualification='Bachelor',
            dob=datetime(2000, 1, 1),
            role='user'
        )
        db.session.add(user)
        db.session.commit()
    
    # Add a sample subject, chapter, quiz, and question if none exist
    if not Subject.query.first():
        subject = Subject(
            name="Mathematics",
            description="A subject that deals with numbers and logic."
        )
        db.session.add(subject)
        db.session.commit()

        chapter = Chapter(
            name="Algebra",
            description="Introduction to algebraic expressions.",
            subject_id=subject.id
        )
        db.session.add(chapter)
        db.session.commit()

        quiz = Quiz(
            title="Mid Sem",
            subject_id=subject.id,  # Include subject_id
            chapter_id=chapter.id,
            date_of_quiz=datetime(2025, 5, 15),
            time_duration="00:30",
            remarks="Basic Algebra Quiz",
        )
        db.session.add(quiz)
        db.session.commit()


        question = Question(
            quiz_id=quiz.id,
            question_statement="What is the value of x in 2x + 3 = 7?",
            option1="1",
            option2="2",
            option3="3",
            option4="4",
            correct_option="2"
        )
        db.session.add(question)
        db.session.commit()


app = create_app()

from controllers.home import home_bp
app.register_blueprint(home_bp)

from controllers.user import user_bp
app.register_blueprint(user_bp)

from controllers.admin import *

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

