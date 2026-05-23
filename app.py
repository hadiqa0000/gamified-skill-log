from flask import Flask, render_template, request, redirect, session, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "dev_secret_key_change_later"

def init_db():
    with sqlite3.connect("users.db") as conn:
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
                "INSERT INTO users (username, password) VALUES (?, ?)",
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

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    with sqlite3.connect("users.db") as conn:
        cursor = conn.cursor()
      
        cursor.execute("SELECT total_points FROM users WHERE id = ?", (session["user_id"],))
        user_points = cursor.fetchone()[0]
        
        
        cursor.execute("""
            SELECT s.*, u.username as creator_name,
                   (SELECT COUNT(*) FROM tasks WHERE skill_id = s.id AND is_active = 1) as task_count
            FROM skills s
            JOIN users u ON s.created_by = u.id
            WHERE s.is_active = 1
            ORDER BY s.created_at DESC
        """)
        skills = cursor.fetchall()
        
        
        

       
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
        return redirect(url_for("login"))
    
    if request.method == "POST":
        name = request.form["name"].strip()
        description = request.form["description"].strip()
        
        if not name:
            flash("Skill name required", "error")
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
        
        
        cursor.execute("""
            SELECT t.*, u.username as creator_name,
                   (SELECT COUNT(*) FROM task_completions WHERE task_id = t.id) as completion_count
            FROM tasks t
            JOIN users u ON t.created_by = u.id
            WHERE t.skill_id = ? AND t.is_active = 1
            ORDER BY t.created_at DESC
        """, (skill_id,))
        tasks = cursor.fetchall()
        
       
        completed_tasks = set()
        cursor.execute("""
            SELECT task_id FROM task_completions 
            WHERE user_id = ?
        """, (session["user_id"],))
        for row in cursor.fetchall():
            completed_tasks.add(row[0])
        
        
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
        return redirect(url_for("login"))
    
    with sqlite3.connect("users.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT created_by FROM skills WHERE id = ?", (skill_id,))
        skill = cursor.fetchone()
        
        
        
        if not skill:
            flash("Skill not found", "error")
            return redirect(url_for("dashboard"))
        
        if skill[0] != session["user_id"]:
            flash("You can only add tasks to your own skills", "error")
            return redirect(url_for("view_skill", skill_id=skill_id))
    
    if request.method == "POST":
        title = request.form["title"].strip()
        description = request.form["description"].strip()
        points = int(request.form.get("points", 10))
        
        
       if not title:
            flash("Task title required", "error")
            return render_template("add_task.html", skill_id=skill_id)
        
       with sqlite3.connect("users.db") as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO tasks (skill_id, title, description, points, created_by) VALUES (?, ?, ?, ?, ?)",
                (skill_id, title, description, points, session["user_id"])
                
                )
                
                conn.commit()
                
            flash("task added succesfully!", "success")
            return redirect(url_for("view_skill", skill_id=skill_id))
            
         return render_template("add_task.html", skill_id=skill_id)
         
         








@app.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("username", None)
    flash("You have been logged out", "info")
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
