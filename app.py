from flask import Flask, render_template, request, redirect, session, url_for, flash
from db import get_db
from services.skills_service import (
    create_skill, 
    get_skill_by_id, 
    get_all_active_skills,
    delete_skill,
    get_tasks_for_skill,
    user_has_completed_tasks_in_skill
)
from services.user_service import (
    register_user, 
    login_user, 
    get_user_points, 
    get_global_leaderboard, 
    get_user_completed_tasks,
    get_skill_leaderboard,
    get_all_skills_leaderboard
)
from services.task_service import complete_task, add_task, delete_task, get_task_details

app = Flask(__name__)
app.secret_key = "dev_secret_key_change_later"

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        total_points INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS skills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        created_by INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT 1,
        FOREIGN KEY (created_by) REFERENCES users (id)
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        skill_id INTEGER,
        title TEXT NOT NULL,
        description TEXT,
        points INTEGER DEFAULT 10,
        created_by INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT 1,
        FOREIGN KEY (skill_id) REFERENCES skills (id),
        FOREIGN KEY (created_by) REFERENCES users (id)
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS task_completions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER,
        user_id INTEGER,
        completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        points_awarded INTEGER,
        FOREIGN KEY (task_id) REFERENCES tasks (id),
        FOREIGN KEY (user_id) REFERENCES users (id),
        UNIQUE(task_id, user_id)
    )
    """)
    
    conn.commit()

init_db()

@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()
        
        conn = get_db()
        user_id, status, error = register_user(username, password, conn)
        
        if status == "success":
            conn.commit()
            session["user_id"] = user_id
            session["username"] = username
            flash("Registration successful!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash(error, "error")
    
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()
        
        conn = get_db()
        user, status, error = login_user(username, password, conn)
        
        if status == "success":
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash(f"Welcome back, {username}!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash(error, "error")
    
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    conn = get_db()
    
    user_points = get_user_points(session["user_id"], conn)
    skills = get_all_active_skills(conn)
    recent_completions = get_user_completed_tasks(session["user_id"], conn)[:10]
    
    return render_template("dashboard.html",
                         username=session["username"],
                         user_points=user_points,
                         skills=skills,
                         recent_completions=recent_completions)

@app.route("/create_skill", methods=["GET", "POST"])
def create_skill():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    if request.method == "POST":
        name = request.form["name"].strip()
        description = request.form["description"].strip()
        
        conn = get_db()
        skill_id, status, error = create_skill(name, description, session["user_id"], conn)
        
        if status == "success":
            conn.commit()
            flash(f"Skill '{name}' created successfully!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash(error, "error")
    
    return render_template("create_skill.html")

@app.route("/skill/<int:skill_id>")
def view_skill(skill_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    conn = get_db()
    
    skill = get_skill_by_id(skill_id, conn)
    
    if not skill:
        flash("Skill not found", "error")
        return redirect(url_for("dashboard"))
    
    tasks = get_tasks_for_skill(skill_id, conn)
    completed_tasks = user_has_completed_tasks_in_skill(session["user_id"], skill_id, conn)
    leaderboard = get_skill_leaderboard(skill_id, conn, 10)
    
    return render_template("skill.html", 
                         skill=skill, 
                         tasks=tasks, 
                         completed_tasks=completed_tasks,
                         leaderboard=leaderboard)

# THIS IS THE CORRECT ADD_TASK ROUTE - KEEP ONLY THIS ONE
@app.route("/add_task/<int:skill_id>", methods=["GET", "POST"])
def add_task(skill_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    if request.method == "POST":
        title = request.form["title"].strip()
        description = request.form["description"].strip()
        points = int(request.form.get("points", 10))
        
        if not title:
            flash("Task title required", "error")
            return render_template("add_task.html", skill_id=skill_id)
        
        conn = get_db()
        task_id, status, error = add_task(skill_id, title, description, points, session["user_id"], conn)
        
        if status == "success":
            conn.commit()
            flash("Task added successfully!", "success")
            return redirect(url_for("view_skill", skill_id=skill_id))
        else:
            flash(error, "error")
            return render_template("add_task.html", skill_id=skill_id)
    
    return render_template("add_task.html", skill_id=skill_id)

@app.route("/complete_task/<int:task_id>")
def complete_task_route(task_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    conn = get_db()
    points, status, skill_id = complete_task(session["user_id"], task_id, conn)
    
    if status == "success":
        conn.commit()
        flash(f"Task completed! You earned {points} points!", "success")
        return redirect(url_for("view_skill", skill_id=skill_id))
    elif status == "already_completed":
        flash("You've already completed this task!", "warning")
        task = get_task_details(task_id, conn)
        if task:
            return redirect(url_for("view_skill", skill_id=task["skill_id"]))
        return redirect(url_for("dashboard"))
    else:
        flash("Task not found or inactive", "error")
        return redirect(url_for("dashboard"))

@app.route("/delete_task/<int:task_id>")
def delete_task_route(task_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    conn = get_db()
    status, skill_id, task_title, error = delete_task(task_id, session["user_id"], conn)
    
    if status == "success":
        conn.commit()
        flash(f"Task '{task_title}' has been expired", "success")
        return redirect(url_for("view_skill", skill_id=skill_id))
    else:
        flash(error, "error")
        return redirect(url_for("dashboard"))

@app.route("/delete_skill/<int:skill_id>")
def delete_skill_route(skill_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    conn = get_db()
    status, skill_name, error = delete_skill(skill_id, session["user_id"], conn)
    
    if status == "success":
        conn.commit()
        flash(f"Skill '{skill_name}' has been deleted", "success")
    else:
        flash(error, "error")
    
    return redirect(url_for("dashboard"))

@app.route("/completed_tasks")
def completed_tasks():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    conn = get_db()
    completed_tasks = get_user_completed_tasks(session["user_id"], conn)
    
    return render_template("completed_tasks.html", completed_tasks=completed_tasks)

@app.route("/leaderboard")
def leaderboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    conn = get_db()
    global_leaderboard = get_global_leaderboard(20, conn)
    skill_leaderboards = get_all_skills_leaderboard(conn)
    
    return render_template("leaderboard.html",
                         global_leaderboard=global_leaderboard,
                         skill_leaderboards=skill_leaderboards)

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("username", None)
    flash("You have been logged out", "info")
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
