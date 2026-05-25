from flask import Flask, render_template, request, redirect, session, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

def init_db():
    with sqlite3.connect("users.db") as conn:
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Add total_points column if it doesn't exist
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN total_points INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        # Skills table
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
        
        # Tasks table
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
        
        # Task completions table
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
        
        # User skill points table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_skill_points (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            skill_id INTEGER,
            points INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (skill_id) REFERENCES skills (id),
            UNIQUE(user_id, skill_id)
        )
        """)
        
        conn.commit()
        
        # Initialize total_points for existing users
        cursor.execute("UPDATE users SET total_points = 0 WHERE total_points IS NULL")
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
        
        if not username or not password:
            flash("Username and password required", "error")
            return render_template("register.html")
        
        with sqlite3.connect("users.db") as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            existing_user = cursor.fetchone()
            
            if existing_user:
                flash("Username already exists", "error")
                return render_template("register.html")
            
            hashed_password = generate_password_hash(password)
            cursor.execute(
    "INSERT INTO users (username, password, total_points) VALUES (?, ?, 0)",
    (username, hashed_password)
)
            conn.commit()
            
            user_id = cursor.lastrowid
            session["user_id"] = user_id
            session["username"] = username
        
        flash("Registration successful!", "success")
        return redirect(url_for("dashboard"))
    
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()
        
        if not username or not password:
            flash("Username and password required", "error")
            return render_template("login.html")
        
        with sqlite3.connect("users.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
        
        if user and check_password_hash(user[2], password):
            session["user_id"] = user[0]
            session["username"] = user[1]
            flash(f"Welcome back, {username}!", "success")
            return redirect(url_for("dashboard"))
        
        flash("Invalid credentials", "error")
    
    return render_template("login.html")
    
    
    
    
@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect(url_for("login"))

    with sqlite3.connect("users.db") as conn:
        cursor = conn.cursor()

        # user info
        cursor.execute("""
            SELECT id, username, total_points, created_at
            FROM users
            WHERE id = ?
        """, (session["user_id"],))
        user = cursor.fetchone()

        # skills created by user
        cursor.execute("""
            SELECT id, name, created_at
            FROM skills
            WHERE created_by = ?
            ORDER BY created_at DESC
        """, (session["user_id"],))
        skills = cursor.fetchall()

        # tasks completed by user
        cursor.execute("""
            SELECT COUNT(*)
            FROM task_completions
            WHERE user_id = ?
        """, (session["user_id"],))
        completed_count = cursor.fetchone()[0]

    return render_template(
        "profile.html",
        user=user,
        skills=skills,
        completed_count=completed_count
    )

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    with sqlite3.connect("users.db") as conn:
        cursor = conn.cursor()
        
        # Get user stats
        cursor.execute("SELECT total_points FROM users WHERE id = ?", (session["user_id"],))
        result = cursor.fetchone()
        user_points = result[0] if result else 0
        
        # Get all active skills
        cursor.execute("""
            SELECT s.*, u.username as creator_name,
                   (SELECT COUNT(*) FROM tasks WHERE skill_id = s.id AND is_active = 1) as task_count
            FROM skills s
            JOIN users u ON s.created_by = u.id
            WHERE s.is_active = 1
            ORDER BY s.created_at DESC
        """)
        skills = cursor.fetchall()
        
        # Get recent completions
        cursor.execute("""
            SELECT tc.*, t.title, u.username, s.name as skill_name, s.id as skill_id
            FROM task_completions tc
            JOIN tasks t ON tc.task_id = t.id
            JOIN users u ON tc.user_id = u.id
            JOIN skills s ON t.skill_id = s.id
            ORDER BY tc.completed_at DESC
            LIMIT 10
        """)
        recent_completions = cursor.fetchall()
        
    return render_template("dashboard.html", 
                         username=session["username"],
                         user_points=user_points,
                         skills=skills,
                         recent_completions=recent_completions)

@app.route("/create_skill", methods=["GET", "POST"])
def create_skill():
    if "user_id" not in session:
        flash("Please login to create a skill", "error")
        return redirect(url_for("login"))
    
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        
        if not name:
            flash("Skill name is required", "error")
            return render_template("create_skill.html")
        
        with sqlite3.connect("users.db") as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO skills (name, description, created_by) VALUES (?, ?, ?)",
                (name, description, session["user_id"])
            )
            conn.commit()
        
        flash(f"Skill '{name}' created successfully!", "success")
        return redirect(url_for("dashboard"))
    
    return render_template("create_skill.html")

@app.route("/skill/<int:skill_id>")
def view_skill(skill_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    with sqlite3.connect("users.db") as conn:
        cursor = conn.cursor()
        
        # Get skill details
        cursor.execute("""
            SELECT s.*, u.username as creator_name
            FROM skills s
            JOIN users u ON s.created_by = u.id
            WHERE s.id = ? AND s.is_active = 1
        """, (skill_id,))
        skill = cursor.fetchone()
        
        if not skill:
            flash("Skill not found", "error")
            return redirect(url_for("dashboard"))
        
        # Get tasks for this skill
        cursor.execute("""
            SELECT t.*, u.username as creator_name,
                   (SELECT COUNT(*) FROM task_completions WHERE task_id = t.id) as completion_count
            FROM tasks t
            JOIN users u ON t.created_by = u.id
            WHERE t.skill_id = ? AND t.is_active = 1
            ORDER BY t.created_at DESC
        """, (skill_id,))
        tasks = cursor.fetchall()
        
        # Check which tasks user has completed
        completed_tasks = set()
        cursor.execute("""
            SELECT task_id FROM task_completions 
            WHERE user_id = ?
        """, (session["user_id"],))
        for row in cursor.fetchall():
            completed_tasks.add(row[0])
        
        # Get leaderboard for this skill
        cursor.execute("""
            SELECT u.username, usp.points
            FROM user_skill_points usp
            JOIN users u ON usp.user_id = u.id
            WHERE usp.skill_id = ?
            ORDER BY usp.points DESC
            LIMIT 10
        """, (skill_id,))
        leaderboard = cursor.fetchall()
        
    return render_template("skill.html", 
                         skill=skill, 
                         tasks=tasks, 
                         completed_tasks=completed_tasks,
                         leaderboard=leaderboard)

@app.route("/add_task/<int:skill_id>", methods=["GET", "POST"])
def add_task(skill_id):
    if "user_id" not in session:
        flash("Please login to add tasks", "error")
        return redirect(url_for("login"))
    
    # Verify skill exists and user owns it
    with sqlite3.connect("users.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name, created_by, is_active FROM skills WHERE id = ?", (skill_id,))
        skill = cursor.fetchone()
        
        if not skill:
            flash("Skill not found", "error")
            return redirect(url_for("dashboard"))
        
        if skill[2] == 0:
            flash("This skill has been deleted", "error")
            return redirect(url_for("dashboard"))
        
        if skill[1] != session["user_id"]:
            flash("You can only add tasks to your own skills", "error")
            return redirect(url_for("view_skill", skill_id=skill_id))
    
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        points = int(request.form.get("points", 10))
        
        if not title:
            flash("Task title is required", "error")
            return render_template("add_task.html", skill_id=skill_id, skill_name=skill[0])
        
        if points < 1:
            points = 1
        if points > 1000:
            points = 1000
        
        with sqlite3.connect("users.db") as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO tasks (skill_id, title, description, points, created_by) VALUES (?, ?, ?, ?, ?)",
                (skill_id, title, description, points, session["user_id"])
            )
            conn.commit()
        
        flash(f"Task '{title}' added successfully with {points} points!", "success")
        return redirect(url_for("view_skill", skill_id=skill_id))
    
    return render_template("add_task.html", skill_id=skill_id, skill_name=skill[0])

@app.route("/complete_task/<int:task_id>")
def complete_task(task_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    with sqlite3.connect("users.db") as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT t.id, t.skill_id, t.title, t.description,
                   t.points, t.created_by, t.created_at, t.is_active,
                   s.id as skill_id
            FROM tasks t
            JOIN skills s ON t.skill_id = s.id
            WHERE t.id = ? AND t.is_active = 1
        """, (task_id,))

        task = cursor.fetchone()

        if not task:
            flash("Task not found or inactive", "error")
            return redirect(url_for("dashboard"))

        task_id_db = task[0]
        skill_id = task[1]
        points_awarded = task[4]   # FIXED

        cursor.execute("""
            SELECT 1 FROM task_completions
            WHERE task_id = ? AND user_id = ?
        """, (task_id, session["user_id"]))

        if cursor.fetchone():
            flash("Already completed", "warning")
            return redirect(url_for("view_skill", skill_id=skill_id))

        cursor.execute("""
            INSERT INTO task_completions (task_id, user_id, points_awarded)
            VALUES (?, ?, ?)
        """, (task_id, session["user_id"], points_awarded))

        cursor.execute("""
    UPDATE users
    SET total_points = COALESCE(total_points, 0) + ?
    WHERE id = ?
""", (points_awarded, session["user_id"]))

        cursor.execute("""
            INSERT INTO user_skill_points (user_id, skill_id, points)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, skill_id)
            DO UPDATE SET points = points + ?
        """, (session["user_id"], skill_id, points_awarded, points_awarded))

        conn.commit()

    flash(f"Task completed! +{points_awarded} points", "success")
    return redirect(url_for("view_skill", skill_id=skill_id))

@app.route("/delete_task/<int:task_id>")
def delete_task(task_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    with sqlite3.connect("users.db") as conn:
        cursor = conn.cursor()
        
        # Check if user owns the task
        cursor.execute(
            "SELECT skill_id, title FROM tasks WHERE id = ? AND created_by = ?",
            (task_id, session["user_id"])
        )
        task = cursor.fetchone()
        
        if not task:
            flash("Task not found or you don't have permission to delete it", "error")
            return redirect(url_for("dashboard"))
        
        # Soft delete the task
        cursor.execute(
            "UPDATE tasks SET is_active = 0 WHERE id = ?",
            (task_id,)
        )
        conn.commit()
    
    flash(f"Task '{task[1]}' has been expired", "success")
    return redirect(url_for("view_skill", skill_id=task[0]))

@app.route("/delete_skill/<int:skill_id>")
def delete_skill(skill_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    with sqlite3.connect("users.db") as conn:
        cursor = conn.cursor()
        
        # Check if user owns the skill
        cursor.execute(
            "SELECT name FROM skills WHERE id = ? AND created_by = ?",
            (skill_id, session["user_id"])
        )
        skill = cursor.fetchone()
        
        if not skill:
            flash("Skill not found or you don't have permission to delete it", "error")
            return redirect(url_for("dashboard"))
        
        # Soft delete the skill and its tasks
        cursor.execute("UPDATE skills SET is_active = 0 WHERE id = ?", (skill_id,))
        cursor.execute("UPDATE tasks SET is_active = 0 WHERE skill_id = ?", (skill_id,))
        conn.commit()
    
    flash(f"Skill '{skill[0]}' has been deleted", "success")
    return redirect(url_for("dashboard"))

@app.route("/completed_tasks")
def completed_tasks():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    with sqlite3.connect("users.db") as conn:
        cursor = conn.cursor()
        
        # Get all completed tasks for the user
        cursor.execute("""
            SELECT tc.*, t.title, t.description, t.points, 
                   s.name as skill_name, s.id as skill_id,
                   CASE WHEN t.is_active = 0 THEN '(Expired)' ELSE '' END as status
            FROM task_completions tc
            JOIN tasks t ON tc.task_id = t.id
            JOIN skills s ON t.skill_id = s.id
            WHERE tc.user_id = ?
            ORDER BY tc.completed_at DESC
        """, (session["user_id"],))
        completed_tasks = cursor.fetchall()
        
    return render_template("completed_tasks.html", completed_tasks=completed_tasks)

@app.route("/leaderboard")
def leaderboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    with sqlite3.connect("users.db") as conn:
        cursor = conn.cursor()
        
        # Global leaderboard
        cursor.execute("""
            SELECT username, total_points
            FROM users
            ORDER BY total_points DESC
            LIMIT 20
        """)
        global_leaderboard = cursor.fetchall()
        
        # Skills leaderboard
        cursor.execute("""
            SELECT s.id, s.name, u.username, usp.points
            FROM user_skill_points usp
            JOIN skills s ON usp.skill_id = s.id
            JOIN users u ON usp.user_id = u.id
            WHERE s.is_active = 1
            ORDER BY s.name, usp.points DESC
        """)
        skill_leaderboards = cursor.fetchall()
        
    return render_template("leaderboard.html", 
                         global_leaderboard=global_leaderboard,
                         skill_leaderboards=skill_leaderboards)

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out", "info")
    return redirect(url_for("login"))
if __name__ == "__main__":
    app.run(debug=True)
