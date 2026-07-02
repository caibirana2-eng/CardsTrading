from flask import Flask, render_template, redirect, url_for, session, request
import sqlite3, secrets, os

conaccounts = sqlite3.connect('accounts.db', check_same_thread=False)
accountscur = conaccounts.cursor()

concards = sqlite3.connect('cards.db', check_same_thread=False)
cardsearchcur = concards.cursor()

app = Flask(__name__)

app.secret_key = secrets.token_hex(32)

@app.route("/", methods=['GET', 'POST'])
def index():
    if not session.get('user_logged_in'):
        return redirect(url_for("login"))
    image_folder = os.path.join('static', 'bugfixchangenotices')
    bugfixchangenotices = os.listdir(image_folder)
    image_folder = os.path.join('static', 'newsetnotices')
    newsetnotices = os.listdir(image_folder)
    image_folder = os.path.join('static', 'trendingcardnotices')
    trendingcardnotices = os.listdir(image_folder)
    user = session.get('user_logged_in')
    if request.method == "POST":
        if "confirmnavsearch" in request.form:
            session["cardsearchbarresults"] = request.form.get("confirmnavsearch")
            return redirect(url_for("cardsearch"))
    return render_template('index.html', bugfixchangenotices=bugfixchangenotices, newsetnotices=newsetnotices, trendingcardnotices=trendingcardnotices, user=user)

@app.route("/cardsearch", methods=['GET', 'POST'])
def cardsearch():
    if not session.get('user_logged_in'):
        return redirect(url_for("login"))
    cardsearchcur.execute("SELECT cardimg FROM cards")
    showncards = cardsearchcur.fetchall()
    cardsearchcur.execute("SELECT DISTINCT fromset FROM cards")
    sets = cardsearchcur.fetchall()
    if request.method == "POST":
        if "card" in request.form:
            session["cardclicked"] = request.form.get("card")
            return redirect(url_for("individualcards"))
        elif "runfilter" in request.form:
            higherlower = request.form.get("avgpricehigherlower")
            if higherlower == "higher":
                pricehighlow = "<"
            else:
                pricehighlow = ">"
            higherlower = request.form.get("releaseearlylate")
            if higherlower == "later":
                releaseearlylate = ">"
            else:
                releaseearlylate = "<"
            higherlower = request.form.get("dataearlylate")
            if higherlower == "later":
                recencyearlylate = "<"
            else:
                recencyearlylate = ">"
            releaseyear = request.form.get("releaseyear")
            intreleaseyear = int(releaseyear)
            recencyyear = request.form.get("datayear")
            intrecencyyear = int(recencyyear)
            filterset = request.form.get("setfilter")
            if filterset == "anyset":
                query = f"SELECT cardimg FROM cards WHERE avgprice {pricehighlow} ? AND intreleaseyear {releaseearlylate} ? AND intinforecency {recencyearlylate} ?"
                cardsearchcur.execute(query, (request.form.get("priceinput"), intreleaseyear, intrecencyyear))
            else:
                query = f"SELECT cardimg FROM cards WHERE fromset = ? AND avgprice {pricehighlow} ? AND intreleaseyear {releaseearlylate} ? AND intinforecency {recencyearlylate} ?"
                cardsearchcur.execute(query, (filterset, request.form.get("priceinput"), intreleaseyear, intrecencyyear))
            showncards = cardsearchcur.fetchall()
    return render_template('cardsearch.html', showncards=showncards, sets=sets)

@app.route("/individualcards", methods=['GET', 'POST'])
def individualcards():
    if not session.get('user_logged_in'):
        return redirect(url_for("login"))
    cardpage = session.get('cardclicked')
    cardsearchcur.execute("SELECT * FROM cards WHERE cardimg = ?", (cardpage,))
    cardpagedata = cardsearchcur.fetchall()
    cleancardpagedata = cardpagedata[0]
    cardname = cleancardpagedata[0]
    cardreleaseyear = cleancardpagedata[1]
    avgcardprice = cleancardpagedata[2]
    carddatarecency = cleancardpagedata[3]
    carddesc = cleancardpagedata[4]
    cardset = cleancardpagedata[5]
    cardlistings = cleancardpagedata[7]
    cardtrend = cleancardpagedata[8]
    return render_template('individualcards.html', carddatarecency=carddatarecency, cardpage=cardpage, carddesc=carddesc, cardname=cardname, cardreleaseyear=cardreleaseyear, avgcardprice=avgcardprice, cardset=cardset, cardlistings=cardlistings, cardtrend=cardtrend)

@app.route("/login", methods=['GET', 'POST'])
def login():
    error = ""
    if request.method == "POST":
        if "confirmlogin" in request.form:
            infoinput = [request.form.get("usernametype"), request.form.get("passwordtype")]
            accountscur.execute('SELECT * FROM accounts WHERE username = ? AND password = ?', (infoinput[0], infoinput[1]))
            data = accountscur.fetchone()
            if data != None:
                session['user_logged_in'] = infoinput[0]
                return redirect(url_for("index"))
            error = "Incorrect username or password! (Case sensitive)"
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
            accountscur.execute('SELECT * FROM accounts WHERE email = ?', (givenemail,))
            data = accountscur.fetchone()
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
    #Checks if a username is already linked to the given forgotpass email   
    error = ""
    givenemail = session.get('givenemail')
    accountscur.execute('SELECT username FROM accounts WHERE email = ?', (givenemail,))
    pastusername = accountscur.fetchone()
    if pastusername == None:
        cleanpastusername = ""
    else:
        cleanpastusername = pastusername[0]
    if request.method == "POST":
        loweredcleanpastusername = cleanpastusername.lower()
    
        createusername = request.form.get("createusernametype")
        createpassword = request.form.get("createpasswordtype")
        loweredcreateusername = createusername.lower()

        #Creates a collection of every username in the database lowered
        accountscur.execute('SELECT LOWER(username) FROM accounts')
        data = accountscur.fetchall()
        cleandata = (account[0] for account in data)

        #Checks if the username input is either the past username or is not taken 
        if loweredcreateusername in cleandata and loweredcreateusername != loweredcleanpastusername:
            error = "Username is taken!"
        else: 
            if"accdetailsconfirm" in request.form:

                #Just states boundaries for the username and password input. Successful check results in either
                #account creation or the data of the account linked to the given email being updated
                if session.get('emailfor') == "signup":
                    if not 3 <= len(createusername) <= 20:
                        error = "Username must be between 3 and 20 characters long."
                    elif createusername != "".join(filter(str.isalnum, createusername)):
                        error = "Username can only contain alphanumeric characters (a-z), (0-9)."
                    elif len(createpassword) < 10:
                        error = "Password must be at least 10 characters long"
                    else:
                        accountscur.execute('INSERT INTO accounts (username, password, email) VALUES (?, ?, ?)', (createusername, createpassword, givenemail,))
                        conaccounts.commit()
                        return redirect(url_for("login"))
                else:                
                    if not 3 <= len(createusername) <= 20:
                        error = "Username must be between 3 and 20 characters long."
                    elif createusername != "".join(filter(str.isalnum, createusername)):
                        error = "Username can only contain alphanumeric characters (a-z), (0-9)."
                    elif len(createpassword) < 10:
                        error = "Password must be at least 10 characters long"
                    else:
                        accountscur.execute('UPDATE accounts SET username =?, password = ? WHERE email = ?', (createusername, createpassword, givenemail,))
                        conaccounts.commit()
                        return redirect(url_for("login"))
                    
                    #added pastusername=cleanpastusername for recognition rather than recall   
    return render_template('accdetails.html', errormessage=error, pastusername=cleanpastusername)

@app.route("/forgotpass", methods=['GET', 'POST'])
def forgotpass():
    error = ""
    if request.method == "POST":
        if "confirmrecoveryemail" in request.form:

            # Same case here as in /signup route
            givenemail = request.form.get("emailtypeforgot")
            accountscur.execute('SELECT * FROM accounts WHERE email = ?', (givenemail,))
            data = accountscur.fetchone()
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