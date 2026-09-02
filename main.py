from flask import Flask, request, redirect, url_for, render_template, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User, Task
import re

def is_strong_password(password):
    if len(password) < 8:
        return False, "Password must contain at least 8 characters."

    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."

    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."

    if not re.search(r"\d", password):
        return False, "Password must contain at least one number."

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character."

    return True, ""

app = Flask(__name__)
import os

database_url = os.environ.get("DATABASE_URL")

if database_url:
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///taskmanager.db'

app.config['SECRET_KEY'] = os.environ.get(
    'SECRET_KEY',
    'temporary-local-development-key'
)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return "Hello, my task manager is starting!"

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        valid, message = is_strong_password(password)
        if not valid:
            return render_template('signup.html', error=message)

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return render_template('signup.html', error="Username already taken")

        new_user = User(username=username) 
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('signup.html')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        return render_template('login.html', error="Invalid username or password")

    return render_template('login.html')
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return "Logged out"

@app.route('/dashboard')
@login_required
def dashboard():
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', username=current_user.username, tasks=tasks)

@app.route('/tasks', methods=['GET'])
@login_required
def get_tasks():
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    result = ""
    for t in tasks:
        result += f"ID:{t.id} | {t.title} | {t.status} | due:{t.due_date}<br>"
    return result if result else "No tasks yet"

@app.route('/tasks/add', methods=['POST'])
@login_required
def add_task():
    title = request.form['title']
    description = request.form.get('description', '')
    due_date = request.form.get('due_date', '')

    new_task = Task(title=title, description=description, due_date=due_date, user_id=current_user.id)
    db.session.add(new_task)
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/tasks/<int:task_id>/update', methods=['POST'])
@login_required
def update_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        return "Not authorized", 403

    task.status = request.form.get('status', task.status)
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/tasks/<int:task_id>/delete', methods=['POST'])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        return "Not authorized", 403

    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('dashboard'))
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)