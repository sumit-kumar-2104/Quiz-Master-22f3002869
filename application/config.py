import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = "change_this_secret_key"

class LocalDevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(basedir, "../database/quiz_master.sqlite3")

# class Config:
#     SQLITE_DB_DIR = None
#     SQLALCHEMY_DATABASE_URI = None
#     SQLALCHEMY_TRACK_MODIFICATIONS = False
#     DEBUG = False
#     SECRET_KEY = "yourdad"

# class LocalDevelopmentConfig(Config):
#     DEBUG = True
#     SECRET_KEY = "yourdad"
#     SQLITE_DB_DIR = os.path.join(basedir, '../database')
#     SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(SQLITE_DB_DIR, 'quiz_master.sqlite3')
