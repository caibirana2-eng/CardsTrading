from flask import Flask, render_template, redirect, url_for, session, request
import sqlite3, secrets, os

con = sqlite3.connect('accounts.db', check_same_thread=False)
cur = con.cursor()

app = Flask(__name__)

app.secret_key = secrets.token_hex(32)

@app.route("/", methods=['GET', 'POST'])
def index():
    if not session.get('user_logged_in'):
        return redirect(url_for("login"))
    image_folder = os.path.join('static', 'personalnotices')
    personalnotices = os.listdir(image_folder)
    print(personalnotices)
    return render_template('index.html', personalnotices=personalnotices)

@app.route("/login", methods=['GET', 'POST'])
def login():
    error = ""
    if request.method == "POST":
        if "confirmlogin" in request.form:
            infoinput = [request.form.get("usernametype"), request.form.get("passwordtype")]
            cur.execute('SELECT * FROM accounts WHERE username = ? AND password = ?', (infoinput[0], infoinput[1]))
            data = cur.fetchone()
            if data != None:
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
            # using emailtype == "erorrpls" as a placeholder for invalid emails
            # Using a set code since I can't email a random temp code
            givenemail = request.form.get("emailtype")
            cur.execute('SELECT * FROM accounts WHERE email = ?', (givenemail,))
            data = cur.fetchone()
            if request.form.get("emailtype") == "errorpls" or request.form.get("emailtype") == "" or data != None:
                error = "Entered invalid or taken email!"
            else:
                session['givenemail'] = givenemail
                session['emailfor'] = "signup"
                session['emailcode'] = "123456" #supposed to be made with random.randint and made temporary with session flask function
                #followed by send code to given email
                return redirect(url_for("receiveemailcode"))            
    return render_template('signup.html', errormessage=error)

@app.route("/accdetails", methods=['GET', 'POST'])
def makeaccount():
    error = ""
    givenemail = session.get('givenemail')
    cur.execute('SELECT username FROM accounts WHERE email = ?', (givenemail,))
    pastusername = cur.fetchone()
    if pastusername == None:
        pastusername = ""
    if request.method == "POST":
        if "accdetailsconfirm" in request.form:
            createusername = request.form.get("createusernametype")
            createpassword = request.form.get("createpasswordtype")
            cur.execute('SELECT * FROM accounts WHERE username = ?', (createusername,))
            data = cur.fetchone()
            if session.get('emailfor') == "signup":
                if data != None:
                    error = "Username is taken!"
                elif not 3 <= len(createusername) <= 20:
                    error = "Username must be between 3 and 20 characters long."
                elif createusername != "".join(filter(str.isalnum, createusername)):
                    error = "Username can only contain alphanumeric characters (a-z), (0-9)."
                elif len(createpassword) < 10:
                    error = "Password must be at least 10 characters long"
                else:
                    print(createusername, createpassword, session.get('givenemail'))
                    cur.execute('INSERT INTO accounts (username, password, email) VALUES (?, ?, ?)', (createusername, createpassword, givenemail,))
                    con.commit()
                    return redirect(url_for("login"))
            else:                
                if data != None and data != pastusername:
                    error = "Username is taken!"
                elif not 3 <= len(createusername) <= 20:
                    error = "Username must be between 3 and 20 characters long."
                elif createusername != "".join(filter(str.isalnum, createusername)):
                    error = "Username can only contain alphanumeric characters (a-z), (0-9)."
                elif len(createpassword) < 10:
                    error = "Password must be at least 10 characters long"
                else:
                    cur.execute('UPDATE accounts SET username =?, password = ? WHERE email = ?', (createusername, createpassword, givenemail,))
                    con.commit()
                    return redirect(url_for("login"))
                
    cleanpastusername = pastusername.replace("('", "").replace("',)", "")
    cleanpastusername = pastusername[0]
    
    return render_template('accdetails.html', errormessage=error, pastusername=cleanpastusername)

@app.route("/forgotpass", methods=['GET', 'POST'])
def forgotpass():
    error = ""
    if request.method == "POST":
        if "confirmrecoveryemail" in request.form:

            # Same case here as signup page
            givenemail = request.form.get("emailtypeforgot")
            cur.execute('SELECT * FROM accounts WHERE email = ?', (givenemail,))
            data = cur.fetchone()
            if request.form.get("emailtype") == "errorpls" or request.form.get("emailtype") == "" or data == None:
                error = "Entered invalid email!"
            else:
                session['givenemail'] = givenemail
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