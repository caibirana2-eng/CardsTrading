from flask import Flask, render_template, redirect, url_for, session, request
import sqlite3

con = sqlite3.connect('accounts.db')
cur = con.cursor()
cur.execute('SELECT * FROM accounts')
accounts = cur.fetchall()
con.close()

app = Flask(__name__)

emailinput = ""

user_logged_in = False

@app.route("/", methods=['GET', 'POST'])
def index():
    global user_logged_in
    if user_logged_in == False:
        return redirect(url_for("login"))
    return render_template('index.html')

@app.route("/login", methods=['GET', 'POST'])
def login():
    global user_logged_in
    error = ""
    if request.method == "POST":
        if "confirmlogin" in request.form:
            infoinput = [request.form.get("usernametype"), request.form.get("passwordtype")]
            for i in accounts:
                if infoinput[0] == i[0] and infoinput[1] == i[1]:
                    user_logged_in = True
                    return redirect(url_for("index"))
            error = "Incorrect username or password!"
    return render_template('login.html', errormessage=error)

@app.route("/signup", methods=['GET', 'POST'])
def signup():
    error = ""
    if request.method == "POST":
        if "confirmemail" in request.form:

            # code to send email and check if valid, then generate a random code with random.randint would be here. Using a set code since I can't email a random code
            # using emailtype == "erorrpls" or "" just to show the error message working
            emailcode = 
            if request.form.get("emailtype") == "errorpls" or "":
                error = "Entered invalid email!"
            else:
                return redirect(url_for("signupcode"))            
    return render_template('signup.html', errormessage=error)

@app.route("/signupcode", methods=['GET', 'POST'])
def signupcode():
    if request.method == "POST":
        if "confirmcode" in request.form:
            if request.form.get()
    return render_template('signupcode.html')


app.run(host="127.0.0.1", port=5000, debug=True)