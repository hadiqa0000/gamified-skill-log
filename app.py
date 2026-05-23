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
        

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("username", None)
    flash("You have been logged out", "info")
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
