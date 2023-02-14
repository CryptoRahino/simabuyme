from sqlite3 import Cursor
from urllib.parse import urlparse

from flask import Flask, request, render_template, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'


def connect_db():
    conn = sqlite3.connect('urls.db')
    return conn


def get_users_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL
        );
    """)
    conn.commit()
    return conn


def init_db():
    conn = connect_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS urls
                 (text text, original_url text, changed_url text)''')
    conn.commit()
    conn.close()


def change_url(url):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    product = parsed_url.path.split('/')[-1]
    return f'http://buymesima.com/r/{product}'


@app.route('/', methods=['GET', 'POST'])
def index():
    if "username" in session:
        print("Hello, {}! This is the home page.".format(session["username"]))
    else:
        return redirect("/login")
    if request.method == 'POST':
        text = request.form['text']
        url = request.form['url']
        if not url or not text:
            return render_template('index.html', changed_url="Please fill Text and URL fields", records=[])
        conn = sqlite3.connect('urls.db')
        c = conn.cursor()
        changed_url = change_url(url)

        c.execute(f"INSERT INTO urls (text, original_url, changed_url) VALUES (?, ?, ?)", (text, url, changed_url))

        conn.commit()
        records = display_records(c)
        conn.close()
        return render_template('index.html', changed_url=changed_url, records=records)
    records = display_records()
    return render_template('index.html', changed_url=None, records=records)


# @app.route('/display_records')
def display_records(cursor: Cursor = None, close: bool = False):
    conn = None
    if not cursor:
        conn = connect_db()
        cursor = conn.cursor()
        close = True
    cursor.execute("SELECT * FROM urls")
    records = cursor.fetchall()
    if close and conn:
        conn.close()
    return records


@app.route('/delete_record/<record_id>')
def delete_record(record_id):
    conn = connect_db()
    c = conn.cursor()
    c.execute("DELETE FROM urls WHERE text=?", (record_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))


@app.route('/r/<path:path>')
def redirect_sima(path):
    conn = connect_db()
    c = conn.cursor()
    record = c.execute(f"SELECT original_url FROM urls WHERE changed_url like '%{path}%'").fetchone()
    conn.close()
    if record:
        return redirect(record[0])
    else:
        return 'URL not found', 404


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        conn = get_users_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?",
                       (request.form["username"], request.form["password"]))
        user = cursor.fetchone()
        conn.close()
        if user:
            session["username"] = user[1]
            return redirect("/")
        return "Invalid username/password. <a href='/login'>Try again</a>"
    return render_template("form.html", form_action='login', submit_value='Login')


@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    if "username" in session:
        if session["username"] == "admin":
            if request.method == "POST":
                conn = get_users_db()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO users (username, password) VALUES (?,?)",
                               (request.form["username"], request.form["password"]))
                conn.commit()
                conn.close()
                return redirect("/")
            return render_template("form.html", form_action='register', submit_value='Register')
        else:
            return "Access Denied: You must be the admin to access this page"
    else:
        return redirect("/login")


if __name__ == '__main__':
    init_db()
    # app.run(debug=True)
    app.run(host='0.0.0.0')
