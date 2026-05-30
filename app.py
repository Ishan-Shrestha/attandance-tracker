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

# i. USER MODEL
class User(UserMixin, db.Model):
    id = db.Column(db.String(20), unique=True, nullable=False, primary_key=True)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(200), nullable=False)

# ii. ATTANDANCE MODEL
class Attandance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=True)
    teacher_id = db.Column(db.String(20), db.ForeignKey('user.id'), nullable=False)
    student_id = db.Column(db.String(20), db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(10), nullable=False, default='present')

# HELPER FUNCTIONS

# 1. LOAD USERS
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, user_id)

# 2. SEE ATTANDANCE
def load_attandance():
    try:
        if current_user.role == 'teacher':
            data = db.session.execute(db.select(Attandance).where(Attandance.teacher_id == current_user.id)).scalars().all()
            logger.info(f"Attandance retrieved successfully for user: {current_user}")
        else:
            data = db.session.execute(db.select(Attandance).where(Attandance.student_id == current_user.id)).scalars().all()
            logger.info(f"Attandance retrieved successfully for user: {current_user}")
    except Exception as e:
        logger.exception(f"Unable to load data: {e}")
        return "Data Not Found"
    return data

# 3. MARK ATTANDANCE
def mark_attandance(date, teacher_id, student_id, status):
    marked_attandance = Attandance(
        date=date,
        teacher_id = teacher_id,
        student_id=student_id,
        status = status
    )
    db.session.add(marked_attandance)
    db.session.commit()
    logger.info(f"Attandance marked by {teacher_id}")

# 4. USER ADD 
def add_user(id, password, role):
    hashed_pass=bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(
        id = id,
        password = hashed_pass,
        role = role
    )
    db.session.add(new_user)
    db.session.commit()
    logger.info(f"User {id} registered successfully.")
    return "user added successfully."

# 5. VERIFY USER
def verify_user(id, password):
    user = User.query.filter_by(id = id).first()
    if user and bcrypt.check_password_hash(user.password, password):
        logger.info(f"User {id} logged in successfully.")
        return user
    else:
        logger.info(f"Failed login attempt from {id}.")
        return None

# ROUTES

# 1. HOME ROUTE
@app.route('/')
@login_required
def home():
    if current_user.role == 'teacher':
        return redirect('/teacher')
    elif current_user.role == 'student':
        return redirect('/student')

# 2. LOGIN ROUTE
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        id = request.form.get('id','').strip()
        password = request.form.get('password', '').strip()
        user = verify_user(id, password)
        if user:
            login_user(user)
            return redirect('/')
    return render_template('login.html')

# 3. SIGNUP ROUTE
@app.route('/sign_up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        id = request.form.get('id','').strip()
        password = request.form.get('password', '').strip()
        role = request.form.get('role','').strip()
        existing_user = User.query.filter_by(id=id).first()
        if existing_user:
            flash('User already exists in the database.')
            logger.warning(f'Attempt to register with existing user: {id}')
            return redirect('/sign_up')
        add_user(id, password, role)
        return redirect('/login')
    return render_template('sign_up.html')

# 4. LOGOUT ROUTE
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

# 5. TEACHER ROUTE
@app.route('/teacher', methods=['GET','POST'])
@login_required
def teacher():
    if current_user.role!='teacher':
        return redirect('/student')
    data = load_attandance()
    if request.method == 'POST':
        date = request.form.get('date','').strip()
        teacher_id = current_user.id
        student_id = request.form.get('student_id','').strip()
        status = request.form.get('status','').strip()
        mark_attandance(date, teacher_id, student_id, status)
        return redirect('/teacher')
    return render_template('teacher_dashboard.html',data = data)

# 6. STUDENT ROUTE
@app.route('/student')
@login_required
def student():
    data = load_attandance()
    return render_template('student_dashboard.html', data=data)

# APP START
if __name__ == '__main__':
    app.run(debug=True)