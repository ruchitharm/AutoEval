from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import sqlite3
from werkzeug.utils import secure_filename
from ocr import extract_text
from similarity import calculate_similarity

app = Flask(__name__)
app.secret_key = "autoeval_secret_key"

UPLOAD_FOLDER = "uploads"
DATABASE = "database.db"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def init_db():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT NOT NULL,
            subject TEXT NOT NULL,
            model_answer TEXT NOT NULL,
            extracted_text TEXT NOT NULL,
            similarity_score REAL NOT NULL,
            marks REAL NOT NULL
        )
    """)

    cur.execute("SELECT * FROM users WHERE username=?", ("admin",))
    if not cur.fetchone():
        cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", ("admin", "admin123"))

    conn.commit()
    conn.close()


@app.route('/')
def home():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = cur.fetchone()
        conn.close()

        if user:
            session['user'] = username
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid username or password")

    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', user=session['user'])


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        student_name = request.form['student_name']
        subject = request.form['subject']
        model_answer = request.form['model_answer']
        file = request.files['file']

        if file.filename == '':
            flash("No file selected")
            return redirect(url_for('upload'))

        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        extracted_text = extract_text(filepath)
        score = calculate_similarity(extracted_text, model_answer)
        marks = round(score * 10, 2)

        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO evaluations
            (student_name, subject, model_answer, extracted_text, similarity_score, marks)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (student_name, subject, model_answer, extracted_text, score, marks))
        conn.commit()
        conn.close()

        return render_template(
            'result.html',
            student_name=student_name,
            subject=subject,
            extracted_text=extracted_text,
            score=score,
            marks=marks
        )

    return render_template('upload.html')


@app.route('/history')
def history():
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT id, student_name, subject, similarity_score, marks FROM evaluations ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()

    return render_template('history.html', rows=rows)


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))


if __name__ == '__main__':
    init_db()
    app.run(debug=True)