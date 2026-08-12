from flask import Flask, render_template, redirect, url_for, session, request
import sqlite3, secrets, os, re

# Connects to the databases and creates cursors for each
conaccounts = sqlite3.connect('accounts.db', check_same_thread=False)
accountscur = conaccounts.cursor()
concards = sqlite3.connect('cards.db', check_same_thread=False)
cardsearchcur = concards.cursor()
conusersets = sqlite3.connect('usersets.db', check_same_thread=False)
usersetcur = conusersets.cursor()

# Creates the Flask app and sets a secret key for session management
app = Flask(__name__)
app.secret_key = secrets.token_hex(32)


# Selects all sets belonging to a logged in user
def selectallusersets():
    global loggedinusersets, usernameupper, usernamewithletter
    usernamewithletter = "a" + session.get("user_logged_in")
    usernameupper = usernamewithletter.upper()
    likeusernameupper = f"%{usernameupper}%"
    usersetcur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE ?", (likeusernameupper,))
    loggedinusersets = usersetcur.fetchall()

# Defines the route for the index page, which displays new set notices and trending card notices
@app.route("/", methods=['GET', 'POST'])
def index():

    # Checks if the user is logged in, and if not, redirects to the login page
    if not session.get('user_logged_in'):
        return redirect(url_for("login"))

    # Retrieves the image names of new set notices and trending card notices from the static folder and turns them into lists
    image_folder = os.path.join('static', 'newsetnotices')
    newsetnotices = os.listdir(image_folder)
    image_folder = os.path.join('static', 'trendingcardnotices')
    trendingcardnotices = os.listdir(image_folder)

    # Retrieves the logged-in user's username from the session
    user = session.get('user_logged_in')

    # Clears the session variables for set persistence and selected user set name
    session["setpersists"] = None
    session["selectedusersetname"] = None
    session["addorremove"] = "add"


    return render_template('index.html', newsetnotices=newsetnotices, trendingcardnotices=trendingcardnotices, user=user)

@app.route("/cardsearch", methods=['GET', 'POST'])
def cardsearch():

    # Checks if the user is logged in, and if not, redirects to the login page
    if not session.get('user_logged_in'):
        return redirect(url_for("login"))

    
    # Retrieves the distinct names of all cards, card images, set names, release years, and data recency values from the cards database to
    # show as options in the filter bar or to display all cards if no kind of filter is applied
    cardsearchcur.execute("SELECT cardimg FROM cards WHERE cardimg IS NOT NULL")
    storedcards = cardsearchcur.fetchall()
    cardsearchcur.execute("SELECT DISTINCT fromset FROM cards WHERE fromset IS NOT NULL")
    sets = cardsearchcur.fetchall()
    cardsearchcur.execute("SELECT DISTINCT intreleaseyear FROM cards ORDER BY intreleaseyear ASC")
    releaseyears = cardsearchcur.fetchall()

    cardsearchcur.execute("SELECT DISTINCT intinforecency FROM cards ORDER BY intinforecency ASC")
    datayears = cardsearchcur.fetchall()

    # Retrieves the name of the selected user set from the ownsets page, if any 
    # Most significant use is lower down near lines 127-142 
    selectedusersetname = session.get("selectedusersetname")

    if request.method == "POST":

        # If the user clicks on a card, the card's image name is stored in the session and the user is redirected to the individual card page
        # where the card image is used to access card's unique row in the database, collecting its data to be displayed
        if "card" in request.form:
            session["cardclicked"] = request.form.get("card")
            return redirect(url_for("individualcards"))

        # If the user uses the search bar, the search value is compared to all card names in the database and any cards with names that contain the search value are displayed
        elif "confirmnavsearch" in request.form:
            searchvalue = request.form.get("navsearch")
            comparedsearchvalue = f"%{searchvalue}%"
            cardsearchcur.execute("SELECT cardimg FROM cards WHERE cardname LIKE ? AND cardimg IS NOT NULL", (comparedsearchvalue,))
            showncards = cardsearchcur.fetchall()

        # If a set is being viewed from ownsets, the set name is stored in the session and the shown cards are filtered to only show cards that are present in the viewed set
        # The session ensures that the set will persist even if the user navigates directly to the individual card page and then returns to card search 
        elif "viewsetname" in request.form:
            session["selectedusersetname"] = request.form.get("viewsetname")
            selectedusersetname = session.get("selectedusersetname")
            showncards = storedcards

        # A big chunk of code that takes the values of every filter option in the filter bar form
        # Then mashes them into one query that finds the cards fitting the criteria defined by the option values
        elif "runfilter" in request.form:
            higherlower = request.form.get("pricefilter")
            if higherlower == "higher":
                pricehighlow = ">"
            else:
                pricehighlow = "<"
            higherlower = request.form.get("releaseearlylate")
            if higherlower == "later":
                releaseearlylate = ">"
            else:
                releaseearlylate = "<"
            higherlower = request.form.get("dataearlylate")
            if higherlower == "later":
                recencyearlylate = ">"
            else:
                recencyearlylate = "<"
            releaseyear = request.form.get("releaseyear")
            intreleaseyear = int(releaseyear)
            recencyyear = request.form.get("datayear")
            intrecencyyear = int(recencyyear)
            filterset = request.form.get("setfilter")
            if filterset == "anyset":
                query = f"SELECT cardimg FROM cards WHERE avgprice {pricehighlow} ? AND intreleaseyear {releaseearlylate} ? AND intinforecency {recencyearlylate} ?"
                cardsearchcur.execute(query, (request.form.get("priceinput"), intreleaseyear, intrecencyyear))
                showncards = cardsearchcur.fetchall()
            else:
                query = f"SELECT cardimg FROM cards WHERE fromset = ? AND avgprice {pricehighlow} ? AND intreleaseyear {releaseearlylate} ? AND intinforecency {recencyearlylate} ?"
                cardsearchcur.execute(query, (filterset, request.form.get("priceinput"), intreleaseyear, intrecencyyear))
                showncards = cardsearchcur.fetchall()

        # If the user clicks on a new set notice, the set name is extracted from the image name and used to find 
        # all cards in the database that have that set name as their fromset value
        elif "newsets" in request.form:
            removepng = request.form.get("newsets").replace(".png", "")
            unnoticeset = removepng.split("-")
            setname = " ".join(unnoticeset)
            cardsearchcur.execute("SELECT cardimg FROM cards WHERE fromset = ?", (setname,))
            showncards = cardsearchcur.fetchall()
            session["viewingnewsets"] = setname
            session["fromhomepage"] = False

    # Clears new set and own set filter when page is accessed via nav bar (since can only trigger if no requests on cardsearch) 
    # or when the user returns to card search from the individual card page while no set is being viewed (since setpersists is cleared in that case)
    # Also designates add or remove button to add since no set is being viewed
    elif not session.get("setpersists"):
        session["selectedusersetname"] = None
        session["addorremove"] = "add"
        selectedusersetname = session.get("selectedusersetname")
        session["viewingnewsets"] = None
        showncards = storedcards

    # If the user is returning to card search from the individual card page while viewing a set, the set will persist and cards shown 
    # will continue to only be from the viewed set
    else:
        session["setpersists"] = None
        showncards = storedcards

    # If the user is viewing their own set, the add or remove button will be set to remove and the stored cards will be filtered to only show cards 
    # that are present in the viewed set
    if selectedusersetname:
        session["addorremove"] = "remove"

        # Selects all cards that are stored in the viewed set
        # In the html file, showncards only appear if they're in the storedcards list, so this effectively filters the shown cards to only be those that are in the viewed set
        username = session.get("user_logged_in")
        usernamewithletter = "a" + username
        setnamewithletter = selectedusersetname + "a"
        uniquesetname = usernamewithletter.upper() + setnamewithletter.lower()
        usersetcur.execute(f"SELECT storedcards FROM {uniquesetname}")
        storedcards = usersetcur.fetchall()

    # If the user is viewing a new set, the add or remove button will be set to add and the stored cards will be filtered to only show cards that are in the viewed new set
    elif session.get("viewingnewsets"):

        # Selects all cards that have the fromset value of the viewed new set
        # In the html file, showncards only appear if they're in the storedcards list, 
        # so this effectively filters the shown cards to only be those that are in the viewed new set
        cardsearchcur.execute("SELECT cardimg FROM cards WHERE fromset = ?", (session.get("viewingnewsets"),))
        storedcards = cardsearchcur.fetchall()

    return render_template('cardsearch.html', showncards=showncards, sets=sets, selectedsetname=selectedusersetname, storedcards=storedcards, releaseyears=releaseyears, datayears=datayears, viewingnewsets=session.get("viewingnewsets"))

@app.route("/instructionsmanual")
def instructionsmanual():

    # Checks if the user is logged in, and if not, redirects to the login page
    if not session.get('user_logged_in'):
        return redirect(url_for("login"))
    
    return render_template('instructionsmanual.html')

@app.route("/faqs")
def faqs():

    # Checks if the user is logged in, and if not, redirects to the login page
    if not session.get('user_logged_in'):
        return redirect(url_for("login"))
    
    return render_template('faqs.html')

@app.route("/contact", methods=['GET', 'POST'])
def contact():

    # Checks if the user is logged in, and if not, redirects to the login page
    if not session.get('user_logged_in'):
        return redirect(url_for("login"))

    # If the user submits the contact form, checks if both the message and subject fields are filled in and sets messagesent to True if they are, 
    # otherwise sets an error message
    error = ""
    messagesent = False
    if request.method == "POST" and "sendmessageconfirm" in request.form:
        if request.form.get("contactmessage") != "" and request.form.get("messagesubject") != "":
            messagesent = True
        else:
            error = "Both fields must be filled in"

    return render_template('contact.html', messagesent=messagesent, error=error)

@app.route("/usersettings", methods=['GET', 'POST'])
def usersettings():
    alert = ""
    requestingdelete = ""

    # Retrieves the logged-in user's username from the session so that it can be displayed in the username input field 
    # and used to check if the new username input is the same as the old one
    pastusername = session.get('user_logged_in')

    # Checks if the user is logged in, and if not, redirects to the login page
    if not session.get('user_logged_in'):
        return redirect(url_for("login"))

    if request.method == "POST":

        # If the user clicks the logout button, clears the session variable for the logged-in user and redirects to the login page
        if "logout" in request.form:
            session['user_logged_in'] = None
            session["loginalert"] = "Logged out successfully!"
            return redirect(url_for("login"))

        # If the user clicks the delete account button, sets requestingdelete to True so that a confirmation form will be displayed on the page
        if "deleteaccount" in request.form:
            requestingdelete = True

        # If the user confirms the deletion of their account, checks if the confirmation input matches the required string and if it does, 
        # deletes the user's account from the accounts database and all of their sets from the usersets database, 
        # then clears the session variable for the logged-in user and redirects to the login page
        if "deleteaccountconfirm" in request.form:
            if request.form.get("deleteaccountconfirm") == "PleaseDeleteMyAccount":

                # Deletes the user's account from the accounts database and clears the session variable for the logged-in user 
                accountscur.execute("DELETE FROM accounts WHERE username = ?", (session.get('user_logged_in'),))
                conaccounts.commit()

                # Selects all tables belonging to the user
                selectallusersets()

                # Deletes all selected tables
                for sets in loggedinusersets:
                    untupledsets = sets[0]
                    query = f"""DROP TABLE IF EXISTS {untupledsets}"""
                    usersetcur.execute(f"{query}")
                    conusersets.commit()
                
                session["loginalert"] = "Account has been permanently deleted"
                session['user_logged_in'] = None
                return redirect(url_for("login"))
            else:
                alert = "Entered text incorrectly!"
        # Changes user's details in account database if all checks are passed, otherwise sets an alert message to be displayed on the page
        if "settingschangeaccount" in request.form:

            loweredpastusername = pastusername.lower()
            settinginputusername = request.form.get("settinginputusername")
            settinginputpassword = request.form.get("settinginputpassword")
            loweredsettinginputusername = settinginputusername.lower()

            # Creates a collection of every username in the database lowered
            accountscur.execute('SELECT LOWER(username) FROM accounts')
            data = accountscur.fetchall()
            cleandata = (account[0] for account in data)

            # If the user submits the form to change their account details, checks if the new username is taken by a different account or if the new password is too short,
            if loweredsettinginputusername in cleandata and loweredsettinginputusername != loweredpastusername:
                alert = "Username is taken!"
            else:

                # same boundary checks as the one for changing account details in the /accdetails route
                if not 3 <= len(settinginputusername) <= 20:
                    alert = "Username must be between 3 and 20 characters long."
                elif settinginputusername != "".join(filter(str.isalnum, settinginputusername)):
                    alert = "Username can only contain alphanumeric characters (a-z), (0-9)."
                elif len(settinginputpassword) < 8:
                    alert = "Password must be at least 8 characters long"
                else:
                    if pastusername.lower() != settinginputusername.lower():

                        # Selects all tables belonging to the user
                        selectallusersets()
                        
                        # Updates the names of all tables belonging to the user
                        usernamewithletter = "a" + settinginputusername
                        for sets in loggedinusersets:
                            cleansets = sets[0]
                            usersetcur.execute(f"SELECT setname from {cleansets}")
                            pasttable = usersetcur.fetchone()
                            pasttablewithletter = pasttable[0] + "a"
                            changedsetname = usernamewithletter.upper() + pasttablewithletter.lower()
                            query = f"ALTER TABLE {cleansets} RENAME TO {changedsetname}"
                            usersetcur.execute(f"{query}")
                            conusersets.commit()

                    # Changes the user's information in the account database
                    accountscur.execute('UPDATE accounts SET username = ?, password = ? WHERE username = ?', (settinginputusername, settinginputpassword, pastusername,)) 
                    conaccounts.commit()
                    session["user_logged_in"] = settinginputusername
                    pastusername = settinginputusername
                    alert = "Successfully set account details!"         

    return render_template('usersettings.html', pastusername=pastusername, alert=alert, requestingdelete=requestingdelete)

@app.route("/individualcards", methods=['GET', 'POST'])
def individualcards():

    # Checks if the user is logged in, and if not, redirects to the login page
    if not session.get('user_logged_in'):
        return redirect(url_for("login"))

    # If the user clicks on a trending card notice on the homepage, 
    # sets the card page to whichever the trending card clicked is and sets the add or remove button to add since no personal set is being viewed.
    # Also sets a session variable to indicate that the user came from the homepage so that when they return to card search, 
    # they will be redirected to the homepage instead of card search
    if "trendingcards" in request.form:
        session["addorremove"] = "add"
        unnoticetrendingcard = request.form.get("trendingcards").split(",")
        cardpage = unnoticetrendingcard[1]
        session["cardclicked"] = cardpage
        session["fromhomepage"] = True

    # If the user clicks on a card from the card search page, sets the card page to whichever card clicked is 
    else:
        if not request.method == "POST":
            session["fromhomepage"] = False
        cardpage = session.get('cardclicked')

    # Selects all tables belonging to the user
    selectallusersets()
    shownsets = []

    # For each table belonging to the user, checks if the card being viewed is already in that set and if it isn't, 
    # adds the set name to a list of sets to be displayed in the add card form
    for sets in loggedinusersets:
        cleansets = sets[0]
        usersetcur.execute(f"SELECT setname FROM {cleansets}")
        loggedinsetname = usersetcur.fetchone()
        if session.get("addorremove") == "add":
            query = f"SELECT storedcards FROM {cleansets} WHERE storedcards = ?"
            usersetcur.execute(f"{query}", (cardpage,))
            alreadyadded = usersetcur.fetchone()
            if not alreadyadded:
                shownsets.append(loggedinsetname[0])
        else:
            shownsets.append(loggedinsetname[0])
    if shownsets == []:
        shownsets = None

    if request.method == "POST":

        # If the user clicks the add card button, 
        # adds the card to the selected set in the usersets database and redirects to card search (with set filter persisting if viewing new sets) or index 
        # depending on whether the user came from trending card notices or not
        if "addcard" in request.form:
            addchosenset = request.form.get("addchosenset")
            fulluniquesetname = usernameupper + addchosenset.lower() + "a"
            query = f"INSERT INTO {fulluniquesetname} (setname, storedcards) VALUES (?, ?)"
            usersetcur.execute(f"{query}", (None, cardpage))
            conusersets.commit()
            if session.get("fromhomepage"):
                session["fromhomepage"] = None
                return redirect(url_for("index"))
            else:
                if session.get("viewingnewsets"):
                    session["setpersists"] = True
                return redirect(url_for("cardsearch"))

        # If the user clicks the remove card button, 
        # removes the card from the selected set in the usersets database and redirects to card search 
        # with set filter persisting
        if "removecard" in request.form: 

            # The set name is retrieved from the session and used to construct the full unique set name to access
            # the correct table in the usersets database, then the card is removed from that table
            removechosenset = session.get("selectedusersetname")
            removechosenwithletter = removechosenset + "a"
            fulluniquesetname = usernameupper + removechosenwithletter.lower()
            query = f"DELETE FROM {fulluniquesetname} WHERE storedcards = ?"
            usersetcur.execute(f"{query}", (cardpage,))
            conusersets.commit()
            session["setpersists"] = True
            return redirect(url_for("cardsearch"))

        # either redirects to the homepage or card search (with set filter persisting if viewing new sets or an owned set) 
        # depending on whether the user came from trending card notices or not
        if "backnoset" in request.form:
            if session.get("fromhomepage"):
                session["fromhomepage"] = None
                return redirect(url_for("index"))
            else:
                if session.get("viewingnewsets"):
                    session["setpersists"] = True
                return redirect(url_for("cardsearch"))
        if "backset" in request.form:
            session["setpersists"] = True
            return redirect(url_for("cardsearch"))

    # Retrieves the data for the card being viewed from the cards database and stores it in variables to be displayed on the individual card page
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

    return render_template('individualcards.html', carddatarecency=carddatarecency, cardpage=cardpage, carddesc=carddesc, cardname=cardname, cardreleaseyear=cardreleaseyear, avgcardprice=avgcardprice, cardset=cardset, cardlistings=cardlistings, cardtrend=cardtrend, shownsets=shownsets, addorremove=session.get("addorremove"))

@app.route("/login", methods=['GET', 'POST'])
def login():
    alert = ""

    # Shows alerts from other pages if the user is redirected to the login page, such as after logging out or creating an account
    if session.get("loginalert"):
        alert = session.get("loginalert")
        session["loginalert"] = None
    
    if request.method == "POST":

        # If the user submits the login form, checks if the username and password match an account in the accounts database and if they do,
        # sets the session variable for the logged-in user and redirects to the index page, otherwise sets an alert message
        if "confirmlogin" in request.form:
            infoinput = [request.form.get("usernametype"), request.form.get("passwordtype")]
            accountscur.execute('SELECT * FROM accounts WHERE username = ? AND password = ?', (infoinput[0], infoinput[1]))
            data = accountscur.fetchone()
            if data != None:
                session['user_logged_in'] = infoinput[0]
                return redirect(url_for("index"))
            alert = "Incorrect username or password! (Case sensitive)"

    return render_template('login.html', errormessage=alert)

@app.route("/signup", methods=['GET', 'POST'])
def signup():
    error = ""
    if request.method == "POST":
        if "confirmemail" in request.form:

            # code to send email and check if valid, then generate a random teporary code with would be here
            # using emailtype == "erorrpls" as a placeholder for invalid emails
            # Using a set code since I can't email a random temp code
            givenemail = request.form.get("emailtype").lower()
            accountscur.execute('SELECT * FROM accounts WHERE LOWER(email) = ?', (givenemail,))
            data = accountscur.fetchone()
            if request.form.get("emailtype") == "errorpls" or request.form.get("emailtype") == "" or data != None:
                error = "Entered invalid or taken email!"
            else:

                # Sets the session variables for the given email, the purpose of the email (signup), 
                # and a temporary code (which would normally be randomly generated and emailed to the user)
                session['givenemail'] = givenemail
                session['emailfor'] = "signup"

                # supposed to be made with random.randint and made temporary with session flask code
                session['emailcode'] = "123456" 
                # supposed to be followed by send code to given email

                return redirect(url_for("receiveemailcode"))            
    return render_template('signup.html', errormessage=error)

# Not only makes accounts, but can also be used to change account details
@app.route("/accdetails", methods=['GET', 'POST'])
def makeaccount():

    # Checks if a username is already linked to the given forgotpass email   
    error = ""
    givenemail = session.get('givenemail')
    accountscur.execute('SELECT username FROM accounts WHERE email = ?', (givenemail,))
    pastusername = accountscur.fetchone()
    if pastusername == None:
        cleanpastusername = ""
    else:
        cleanpastusername = pastusername[0]
    if request.method == "POST":

        # If the user submits the form to confirm their account details, 
        # checks if the new username is taken by a different account or if the new password is too short,
        # and if all checks pass, either creates a new account or updates the existing account's details in the accounts database
        loweredcleanpastusername = cleanpastusername.lower()
        createusername = request.form.get("createusernametype")
        createpassword = request.form.get("createpasswordtype")
        loweredcreateusername = createusername.lower()

        # Creates a collection of every username in the database lowered
        accountscur.execute('SELECT LOWER(username) FROM accounts')
        data = accountscur.fetchall()
        cleandata = (account[0] for account in data)

        # Checks if the username input is either the past username or is not taken 
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
                    elif len(createpassword) < 8:
                        error = "Password must be at least 8 characters long"
                    else:
                        accountscur.execute('INSERT INTO accounts (username, password, email) VALUES (?, ?, ?)', (createusername, createpassword, givenemail,))
                        conaccounts.commit()
                        session["loginalert"] = "Successfully created account!"
                        return redirect(url_for("login"))
                else:                
                    if not 3 <= len(createusername) <= 20:
                        error = "Username must be between 3 and 20 characters long."
                    elif createusername != "".join(filter(str.isalnum, createusername)):
                        error = "Username can only contain alphanumeric characters (a-z), (0-9)."
                    elif len(createpassword) < 8:
                        error = "Password must be at least 8 characters long"
                    else:
                        if cleanpastusername.lower() != createusername.lower():
                            # Selects all sets owned by the user
                            usernamewithletter = "a" + cleanpastusername
                            usernameupper = usernamewithletter.upper()
                            likeusernameupper = f"%{usernameupper}%"
                            usersetcur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE ?", (likeusernameupper,))
                            loggedoutusersets = usersetcur.fetchall()
                            
                            # Updates the names of all tables belonging to the user
                            for sets in loggedoutusersets:
                                cleansets = sets[0]
                                usersetcur.execute(f"SELECT setname from {cleansets}")
                                pasttable = usersetcur.fetchone()
                                pasttablewithletter = pasttable[0] + "a"
                                usernamewithletter =  "a" + createusername
                                usernameupper = usernamewithletter.upper()
                                likeusernameupper = f"%{usernameupper}%"
                                changedsetname = usernamewithletter.upper() + pasttablewithletter.lower()
                                query = f"ALTER TABLE {cleansets} RENAME TO {changedsetname}"
                                usersetcur.execute(f"{query}")
                                conusersets.commit()

                        # Changes the user's information in the account database
                        accountscur.execute('UPDATE accounts SET username =?, password = ? WHERE email = ?', (createusername, createpassword, givenemail,))
                        conaccounts.commit()
                        session["loginalert"] = "Successfully set account details!"
                        return redirect(url_for("login"))
                    
                    #added pastusername=cleanpastusername to autofill the username input field with the past username if the user is changing their account details
    return render_template('accdetails.html', errormessage=error, pastusername=cleanpastusername)

@app.route("/forgotpass", methods=['GET', 'POST'])
def forgotpass():
    error = ""
    if request.method == "POST":

        # If the user submits the form to confirm their email for password recovery, checks if the email is valid and linked to an account in the accounts database,
        # and if it is, sets the session variables for the given email, the purpose of the email (forgotpass),
        # and a temporary code (which would normally be randomly generated and emailed to the user), then redirects to the receiveemailcode page
        if "confirmrecoveryemail" in request.form:

            # Same case here as in /signup route (pretty much the exact same code, just with different session variable for emailfor)
            givenemail = request.form.get("emailtypeforgot").lower()
            accountscur.execute('SELECT * FROM accounts WHERE LOWER(email) = ?', (givenemail,))
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

    # Checks if the user is trying to signup or change their account details, or if they're trying to recover their password, 
    # and sets the priorpage variable (back link) accordingly
    emailfor = session.get('emailfor')

    error = ""

    # If the user submits the form to confirm the code, checks if the code matches the one stored in the session (will always be 123456) 
    # and redirects to the appropriate page if it does,
    # otherwise sets an error message to be displayed on the page
    if request.method == "POST":
        if "confirmcodeemail" in request.form:
            if request.form.get('codeemail') == session.get('emailcode'):
                return redirect(url_for("makeaccount"))
            else:
                error = "Incorrect Code!"

        # No form for resend code since the website won't actually be sending emails

    return render_template('receiveemailcode.html', errormessage=error, priorpage=emailfor)

@app.route("/ownsets", methods=['GET', 'POST'])
def ownsets():

    # Checks if the user is logged in, and if not, redirects to the login page
    if not session.get('user_logged_in'):
        return redirect(url_for("login"))
    
    error = ""
    session["viewingnewsets"] = False
    username = session.get("user_logged_in")
    usernamewithletter = "a" + username
    if request.method == "POST":

        # If the user confirms the creation of a new set, checks if the set name is valid, 
        # then if valid creates a new table for the set in the usersets database.
        # Else sets an error message to be displayed on the page
        if "confirmmakeset" in request.form:


            # Makes use of alphanumeric filter to account for risk of SQL injection caused by f strings being used in the queries
            # Uses capital username and lower set name joined to help ensure that each table is unique and can be directly linked to individual users
            # Ensures there will always be letters to capitalize / decapitalize in the set and user names to ensure that the capital thing can't just be avoided by someone using only numbers in either name
            # Involves a filter to ensure that the set name is alphanumeric and not too long, and checks if the set name is already taken by the user 
            setname = request.form.get("makesetname").strip()
            setnamewithletter = setname + "a"
            if not setname:
                error = "Please enter a set name"
            elif setname != "".join(filter(str.isalnum, setname)):
                    error = "Set name can only contain alphanumeric characters (a-z), (0-9)"
            elif len(setname) > 20:
                    error = "Set name can only be as long as 20 characters"
            else:
                uniquesetname = usernamewithletter.upper() + setnamewithletter.lower()
                query = f"""SELECT name FROM sqlite_master WHERE type='table' AND name = '{uniquesetname}'"""
                usersetcur.execute(f"{query}")
                matchingtablename = usersetcur.fetchall()
                if matchingtablename:
                    error = "You've already created a set with this name!"
                else:

                    # Creates a uniquely named table, then immediately stores the data of what the set it's for is named, and the exact username of the user who made the set
                    query = f"""CREATE TABLE IF NOT EXISTS {uniquesetname} (setname TEXT, storedcards TEXT)"""
                    usersetcur.execute(f"{query}")
                    query = f"INSERT INTO {uniquesetname} (setname, storedcards) VALUES (?, ?)"
                    usersetcur.execute(f"{query}", (setname, None))
                    conusersets.commit()
        
        # Deletes whichever set the value is assigned to
        if "deleteset" in request.form:
            setname = request.form.get("deletesetname")
            setnamewithletter = setname + "a"
            uniquesetname = usernamewithletter.upper() + setnamewithletter.lower()
            query = f"""DROP TABLE IF EXISTS {uniquesetname}"""
            usersetcur.execute(f"{query}")
            error = f"Successfully deleted set: {setname}"
            conusersets.commit()
            
    # Selects all tables belonging to the user
    selectallusersets()
    shownsets = []

    # Selects the set names from every table belonging to the user and adds them to shown sets
    for sets in loggedinusersets:
        cleansets = sets[0]
        usersetcur.execute(f"SELECT setname FROM {cleansets}")
        loggedinsetname = usersetcur.fetchone()
        shownsets.append(loggedinsetname[0]) 

    return render_template('ownsets.html', error=error, shownsets=shownsets)


app.run(host="127.0.0.1", port=5000, debug=True)