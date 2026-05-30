from flask import Flask, flash, render_template, redirect, request
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
import logging
import os   

# LOGGER CONFIGURATION SETTING
logging.basicConfig(
    filename="info.log",
    format='%(asctime)s %(levelname)s: %(message)s'
)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# PATH VARUABLE
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# FLASK APP STARTUP
app = Flask(__name__)

# APP CONFIGURATIONS
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///project.db'
app.config['SECRET_KEY'] = '1111'

# FEATURES LIBRARY SETUP

#  1. BCRYPT SETUP
bcrypt = Bcrypt(app)

# 2. LOGIN MANAGER SETUP
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# 3. SQL SETUP
class Base(DeclarativeBase):
    pass
db = SQLAlchemy(model_class=Base)
migrate = Migrate(app, db)
db.init_app(app)

# MODEL SETUP

# user model
class User(UserMixin, db.Model):
    id = db.Column(db.String(20), unique=True, nullable=False, primary_key=True)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(200), nullable=False)

# data model
class Attandance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(20), nullable=True)
    teacher_id = db.Column(db.String(20), db.ForeignKey('user.id'), nullable=False)
    student_id = db.Column(db.String(20), db.ForeignKey('user.id'), nullable=False)

