from flask import Flask, request, redirect, url_for, render_template, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User, Task

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///taskmanager.db'
app.config['SECRET_KEY'] = 'change-this-later'

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

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return "Username already taken"

        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        return "Signup successful! Go to /login"

    return '''
        <form method="POST">
            Username: <input name="username"><br>
            Password: <input name="password" type="password"><br>
            <button type="submit">Sign Up</button>
        </form>
    '''

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))

        return "Invalid username or password"

    return '''
        <form method="POST">
            Username: <input name="username"><br>
            Password: <input name="password" type="password"><br>
            <button type="submit">Log In</button>
        </form>
    '''

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