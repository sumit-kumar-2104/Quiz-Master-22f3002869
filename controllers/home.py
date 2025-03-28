from flask import Blueprint, render_template
from models.model import db, User, Quiz, Chapter, Subject

home_bp = Blueprint("home", __name__)

@home_bp.route('/')
def home():
    all_subjects = Subject.query.all()
    all_chapters = Chapter.query.all()
    all_quizzes = Quiz.query.all()
    return render_template('home.html', subjects=all_subjects, chapters=all_chapters, quizzes=all_quizzes)

@home_bp.route('/registeredusers')
def registered_users():
    registered_users = User.query.all()
    return render_template('home.html', users=registered_users)

@home_bp.route('/about')
def about():
    return render_template('about.html')

@home_bp.route('/contact')
def contact():
    return render_template('contact.html')
