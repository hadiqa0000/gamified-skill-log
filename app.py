from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import os
print(os.path.abspath("users.db"))

app = Flask(__name__)
app.secret_key = "dev_secret_key_change_later" #so this is for session management


#first trying with a list approach 

@app.route("/") #this is the main page 
def home():
   if "user" in session:
   	return redirect(url_for("dashboard")) #used to send user to a specific page, it generates a url for "dashboard" function
   return redirect(url_for("login"))
   
   
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()

        # check if user exists
        cursor.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        )

        existing_user = cursor.fetchone()

        if existing_user:
            conn.close()
            return "USER ALREADY EXISTS"

        
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, password)
        )

        conn.commit()
        conn.close()

        session["user"] = username

        return redirect(url_for("dashboard"))

    return render_template("register.html")
	
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE username = ? AND password = ?",
            (username, password)
        )

        user = cursor.fetchone()

        conn.close()

        if user:
            session["user"] = username
            return redirect(url_for("dashboard"))

        return "invalid credentials"

    return render_template("login.html")
	
@app.route("/logout")
def logout():
	session.pop("user", None)
	return redirect(url_for("login"))
	

@app.route("/dashboard")
def dashboard():
	if "user" not in session:
		return redirect(url_for("login"))
		
	return f"Welcome {session['user']}"
	

if __name__ == "__main__":
    app.run(debug=True)
