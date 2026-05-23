from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

print(os.path.abspath("users.db"))

app = Flask(__name__)
app.secret_key = "dev_secret_key_change_later"


def init_db():
    with sqlite3.connect("users.db") as conn:
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
        """)

        conn.commit()


init_db()



@app.route("/")
def home():

    if "user" in session:
        return redirect(url_for("dashboard"))

    return redirect(url_for("login"))



@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"].strip()
        password = request.form["password"].strip()

        # validation
        if not username or not password:
            return "Username and password required"

        with sqlite3.connect("users.db") as conn:

            cursor = conn.cursor()

            # check existing user
            cursor.execute(
                "SELECT * FROM users WHERE username = ?",
                (username,)
            )

            existing_user = cursor.fetchone()

            if existing_user:
                return "USER ALREADY EXISTS"

            # hash password
            hashed_password = generate_password_hash(password)

            # insert user
            cursor.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, hashed_password)
            )

            conn.commit()

        session["user"] = username

        return redirect(url_for("dashboard"))

    return render_template("register.html")




@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"].strip()
        password = request.form["password"].strip()

        if not username or not password:
            return "Username and password required"

        with sqlite3.connect("users.db") as conn:

            cursor = conn.cursor()

            cursor.execute(
                "SELECT * FROM users WHERE username = ?",
                (username,)
            )

            user = cursor.fetchone()

        

        if user and check_password_hash(user[2], password):

            session["user"] = username

            return redirect(url_for("dashboard"))

        return "Invalid credentials"

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect(url_for("login"))

    return f"Welcome {session['user']}"




@app.route("/logout")
def logout():

    session.pop("user", None)

    return redirect(url_for("login"))



if __name__ == "__main__":
    app.run(debug=True)
