from flask import Flask, render_template, request
import sqlite3

app = Flask(__name__)
print(app)

@app.route("/", methods=['GET', 'POST'])
def login():
    bozo = "HI"
    return render_template('login.html', bozobozo=bozo)

app.run(host="127.0.0.1", port=5000, debug=True)