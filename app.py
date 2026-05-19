from flask import Flask, render_template, request, redirect, session, url_for

app = Flask(__name__)
app.secret_key = "dev_secret_key_change_later" #so this is for session management


#first trying with a list approach 
users = {}
@app.route("/")
def home():
   if "users" in session:
   	return redirect(url_for("dashboard")) #used to send user to a specific page, it generates a url for "dashboard" function
   return redirect(url_for("login"))
@app.route("/register", methods=["GET", "POST"])
def register():
	if request.method == "POST":
		username = request.form["username"]
		password = request.form["password"]
		
		if username in users:
			return "USER ALREADY EXISTS"
		
		users[username] = password
		return redirect(url_for("login"))
	return render_template("register.html")
	
@app.route("/login", methods=["GET", "POST"])

def login():
	if request.method == "POST":
		username = request.form["username"]
		password = request.form["password"]
		
		if username in users and users[username] == password:
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
