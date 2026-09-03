import os
import re

from flask import Flask, request, redirect, url_for, render_template
from flask_login import (
    LoginManager,
    login_user,
    login_required,
    logout_user,
    current_user
)

from models import db, User, Task


# -----------------------------------
# PASSWORD VALIDATION
# -----------------------------------

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


# -----------------------------------
# FLASK APP
# -----------------------------------

app = Flask(__name__)


# -----------------------------------
# DATABASE CONFIGURATION
# -----------------------------------

database_url = os.environ.get("DATABASE_URL")

if database_url:
    # Fix old PostgreSQL URL format if needed
    if database_url.startswith("postgres://"):
        database_url = database_url.replace(
            "postgres://",
            "postgresql://",
            1
        )

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url

else:
    # SQLite for Replit/local development
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///taskmanager.db"


app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


# -----------------------------------
# SECRET KEY
# -----------------------------------

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "temporary-local-development-key"
)


# -----------------------------------
# DATABASE INITIALIZATION
# -----------------------------------

db.init_app(app)


# -----------------------------------
# LOGIN MANAGER
# -----------------------------------

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# Create database tables
with app.app_context():
    db.create_all()


# -----------------------------------
# HOME
# -----------------------------------

@app.route("/")
def home():
    return redirect(url_for("login"))


# -----------------------------------
# SIGNUP
# -----------------------------------

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        # Check empty fields
        if not username or not password:
            return render_template(
                "signup.html",
                error="Username and password are required."
            )

        # Strong password validation
        valid, message = is_strong_password(password)

        if not valid:
            return render_template(
                "signup.html",
                error=message
            )

        # Check existing user
        existing_user = User.query.filter_by(
            username=username
        ).first()

        if existing_user:
            return render_template(
                "signup.html",
                error="Username already taken."
            )

        # Create user
        new_user = User(username=username)

        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("signup.html")


# -----------------------------------
# LOGIN
# -----------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(
            username=username
        ).first()

        if user and user.check_password(password):

            login_user(user)

            return redirect(
                url_for("dashboard")
            )

        return render_template(
            "login.html",
            error="Invalid username or password."
        )

    return render_template("login.html")


# -----------------------------------
# LOGOUT
# -----------------------------------

@app.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect(
        url_for("login")
    )


# -----------------------------------
# DASHBOARD
# -----------------------------------

@app.route("/dashboard")
@login_required
def dashboard():

    tasks = Task.query.filter_by(
        user_id=current_user.id
    ).all()

    return render_template(
        "dashboard.html",
        username=current_user.username,
        tasks=tasks
    )


# -----------------------------------
# GET TASKS
# -----------------------------------

@app.route("/tasks", methods=["GET"])
@login_required
def get_tasks():

    tasks = Task.query.filter_by(
        user_id=current_user.id
    ).all()

    result = ""

    for task in tasks:

        result += (
            f"ID: {task.id} | "
            f"{task.title} | "
            f"{task.status} | "
            f"Due: {task.due_date}<br>"
        )

    return result if result else "No tasks yet."


# -----------------------------------
# ADD TASK
# -----------------------------------

@app.route("/tasks/add", methods=["POST"])
@login_required
def add_task():

    title = request.form.get("title", "").strip()

    description = request.form.get(
        "description",
        ""
    ).strip()

    due_date = request.form.get(
        "due_date",
        ""
    )

    if not title:
        return redirect(
            url_for("dashboard")
        )

    new_task = Task(
        title=title,
        description=description,
        due_date=due_date,
        user_id=current_user.id
    )

    db.session.add(new_task)
    db.session.commit()

    return redirect(
        url_for("dashboard")
    )


# -----------------------------------
# UPDATE / MARK TASK DONE
# -----------------------------------

@app.route(
    "/tasks/<int:task_id>/update",
    methods=["POST"]
)
@login_required
def update_task(task_id):

    task = Task.query.get_or_404(task_id)

    # Security: users can update only their own tasks
    if task.user_id != current_user.id:
        return "Not authorized", 403

    task.status = request.form.get(
        "status",
        task.status
    )

    db.session.commit()

    return redirect(
        url_for("dashboard")
    )


# -----------------------------------
# DELETE TASK
# -----------------------------------

@app.route(
    "/tasks/<int:task_id>/delete",
    methods=["POST"]
)
@login_required
def delete_task(task_id):

    task = Task.query.get_or_404(task_id)

    # Security: users can delete only their own tasks
    if task.user_id != current_user.id:
        return "Not authorized", 403

    db.session.delete(task)

    db.session.commit()

    return redirect(
        url_for("dashboard")
    )


# -----------------------------------
# RUN APPLICATION
# -----------------------------------

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=3000,
        debug=True
    )