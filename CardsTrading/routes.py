from flask import Flask, render_template, redirect, url_for, session, request
import sqlite3

con = sqlite3.connect('accounts.db')
cur = con.cursor()
cur.execute('SELECT * FROM accounts')
accounts = cur.fetchall()
con.close()

app = Flask(__name__)

user_logged_in = False

error = ""

@app.route("/", methods=['GET', 'POST'])
def index():
    global user_logged_in
    if user_logged_in == False:
        return redirect(url_for("login"))
    return render_template('index.html')

@app.route("/login", methods=['GET', 'POST'])
def login():
    global user_logged_in, error
    if request.method == "POST":
        if "receiveacclogindata" in request.form:
            infoinput = [request.form.get("usernametype"), request.form.get("passwordtype")]
            for i in accounts:
                if infoinput[0] == i[0] and infoinput[1] == i[1]:
                    user_logged_in = True
                    print("9wq09eqw9eqw9e90qweu0qwe09uqwe09uqw09euqw9e0uq90weuq90uw90eq9w0eq9weuwe9qw0e0qw")
                    return redirect(url_for("index"))
                else:
                    print("8wq09eqw9eqw9e90qweu0qwe09uqwe09uqw09euqw9e0uq90weuq90uw90eq9w0eq9weuwe9qw0e0qw")
            error = "Incorrect username or password!"
        else:
            print("AHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH")
    return render_template('login.html', errormessage=error)

@app.route("/signup", methods=['GET', 'POST'])
def signup():
    return render_template('signup.html')

app.run(host="127.0.0.1", port=5000, debug=True)