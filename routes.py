from flask import Flask, render_template, redirect, url_for, session, request
import sqlite3

con = sqlite3.connect('accounts.db')
cur = con.cursor()
cur.execute('SELECT * FROM accounts')
accounts = cur.fetchall()
con.close()

app = Flask(__name__)

emailinput = ""

session['user_logged_in'] = ""

@app.route("/", methods=['GET', 'POST'])
def index():
    if session.get['user_logged_in'] == "":
        return redirect(url_for("login"))
    return render_template('index.html')

@app.route("/login", methods=['GET', 'POST'])
def login():
    error = ""
    if request.method == "POST":
        if "confirmlogin" in request.form:
            infoinput = [request.form.get("usernametype"), request.form.get("passwordtype")]

            #Currently uses a python variable set to a two dimensional list, which the code fully loops over to find a match
            #Not very efficient and doesn't directly use sql. Will change later if I have time
            for i in accounts:
                if infoinput[0] == i[0] and infoinput[1] == i[1]:
                    session['user_logged_in'] = infoinput[0]
                    return redirect(url_for("index"))
            error = "Incorrect username or password!"
    return render_template('login.html', errormessage=error)

@app.route("/signup", methods=['GET', 'POST'])
def signup():
    global accounts
    error = ""
    if request.method == "POST":
        if "confirmemail" in request.form:

            # code to send email and check if valid, then generate a random teporary code with would be here
            # using emailtype == "erorrpls" or "" just to show the error message working
            # Using a set code since I can't email a random temp code
            if request.form.get("emailtype") == "errorpls" or request.form.get("emailtype") == "":
                error = "Entered invalid or taken email!"
            else:
                

                session['emailcode'] = "123456" #supposed to be made with random.randint and made temporary with session flask function
                #followed by send code to given email
                return redirect(url_for("signupcode"))            
    return render_template('signup.html', errormessage=error)

@app.route("/signupcode", methods=['GET', 'POST'])
def signupcode():
    error = ""
    if request.method == "POST":
        if "confirmcodeemail" in request.form:
            if request.form.get('codeemail') == session.get['emailcode']:
                return redirect(url_for("makeaccount"))
            else:
                error = "Incorrect Code!"
        # No form for resend code since the website won't actually be sending emails
    return render_template('signupcode.html', errormessage=error)

@app.route("/makeaccount", methods=['GET', 'POST'])
def makeaccount():
    error = ""
    return render_template('makeaccount.html', errormessage=error)


app.run(host="127.0.0.1", port=5000, debug=True)