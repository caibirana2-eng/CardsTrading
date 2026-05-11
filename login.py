from flask import Flask, render_template, request
import sqlite3

con = sqlite3.connect('accounts.db')
cur = con.cursor()
cur.execute('SELECT * FROM accounts')
accounts = cur.fetchall()
con.close()

print(accounts)

app = Flask(__name__)

@app.route("/", methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        if "usernametype" in request.form or "passwordtype" in request.form or "confirmlogin" in request.form:
            print(request.form.get("usernametype"))
            print(request.form.get("passwordtype"))
    return render_template('login.html')

app.run(host="127.0.0.1", port=5000, debug=True)