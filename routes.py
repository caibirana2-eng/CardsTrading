from flask import Flask, render_template, redirect, url_for, session, request
import sqlite3
import secrets

con = sqlite3.connect('accounts.db')
cur = con.cursor()

app = Flask(__name__)

app.secret_key = secrets.token_hex(32)

@app.route("/", methods=['GET', 'POST'])
def index():
    if not session.get('user_logged_in'):
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
            cur.execute(f'SELECT * FROM accounts WHERE ? = username AND ? = password', (infoinput[0], infoinput[1]))
                if 
                    session['user_logged_in'] = infoinput[0]
                    print(session.get('user_logged_in'))
                    return redirect(url_for("index"))
            error = "Incorrect username or password!"
    return render_template('login.html', errormessage=error)

@app.route("/signup", methods=['GET', 'POST'])
def signup():
    error = ""
    if request.method == "POST":
        if "confirmemail" in request.form:

            # code to send email and check if valid, then generate a random teporary code with would be here
            # using emailtype == "erorrpls" or "" just to show the error message working
            # Using a set code since I can't email a random temp code
            if request.form.get("emailtype") == "errorpls" or request.form.get("emailtype") == "":
                error = "Entered invalid or taken email!"
            else:
                
                session['emailfor'] = "signup"
                session['emailcode'] = "123456" #supposed to be made with random.randint and made temporary with session flask function
                #followed by send code to given email
                return redirect(url_for("receiveemailcode"))            
    return render_template('signup.html', errormessage=error)

@app.route("/accdetails", methods=['GET', 'POST'])
def makeaccount():
    error = ""
    return render_template('accdetails.html', errormessage=error)

@app.route("/forgotpass", methods=['GET', 'POST'])
def forgotpass():
    error = ""
    if request.method == "POST":
        if "confirmrecoveryemail" in request.form:

            # Exact same case here as signup page
            if request.form.get("emailtypeforgot") == "errorpls" or request.form.get("emailtypeforgot") == "":
                error = "Entered invalid or taken email!"
            else:
                
                session['emailfor'] = "forgotpass"
                session['emailcode'] = "123456" 
                return redirect(url_for("receiveemailcode"))            
    return render_template('forgotpass.html', errormessage=error)

@app.route("/receiveemailcode", methods=['GET', 'POST'])
def receiveemailcode():
    emailfor = session.get('emailfor')
    error = ""
    if request.method == "POST":
        if "confirmcodeemail" in request.form:
            if request.form.get('codeemail') == session.get('emailcode'):
                return redirect(url_for("makeaccount"))
            else:
                error = "Incorrect Code!"
        # No form for resend code since the website won't actually be sending emails
    return render_template('receiveemailcode.html', errormessage=error, priorpage=emailfor)


app.run(host="127.0.0.1", port=5000, debug=True)