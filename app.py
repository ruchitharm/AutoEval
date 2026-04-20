from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "autoeval_secret_key"

DATABASE = "database.db"
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
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
            register_number TEXT NOT NULL,
            subject TEXT NOT NULL,
            model_answer TEXT NOT NULL,
            extracted_text TEXT NOT NULL,
            similarity_score REAL NOT NULL,
            marks REAL NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def home():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            flash("Please enter both username and password")
            return redirect(url_for("login"))

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM users WHERE username = ? AND password = ?",
            (username, password)
        )
        user = cur.fetchone()
        conn.close()

        if user:
            session["user"] = username
            flash("Login successful")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            flash("Please fill all fields")
            return redirect(url_for("register"))

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = ?", (username,))
        existing_user = cur.fetchone()

        if existing_user:
            conn.close()
            flash("Username already exists")
            return redirect(url_for("register"))

        cur.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, password)
        )
        conn.commit()
        conn.close()

        flash("Registration successful. Please login.")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        flash("Please login first")
        return redirect(url_for("login"))

    return render_template("dashboard.html", user=session["user"])


@app.route("/upload", methods=["GET", "POST"])
def upload():
    if "user" not in session:
        flash("Please login first")
        return redirect(url_for("login"))

    if request.method == "POST":
        student_name = request.form.get("student_name", "").strip()
        register_number = request.form.get("register_number", "").strip()
        subject = request.form.get("subject", "").strip()
        model_answer = request.form.get("model_answer", "").strip()
        file = request.files.get("file")

        if not student_name or not register_number or not subject or not model_answer:
            flash("Please fill all fields")
            return redirect(url_for("upload"))

        if not file or file.filename == "":
            flash("Please choose an image file")
            return redirect(url_for("upload"))

        if not allowed_file(file.filename):
            flash("Only PNG, JPG, and JPEG files are allowed")
            return redirect(url_for("upload"))

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        extracted_text = "Sample extracted text from uploaded answer sheet"
        similarity_score = 0.85
        marks = round(similarity_score * 10, 2)

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO evaluations (
                student_name,
                register_number,
                subject,
                model_answer,
                extracted_text,
                similarity_score,
                marks
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            student_name,
            register_number,
            subject,
            model_answer,
            extracted_text,
            similarity_score,
            marks
        ))
        conn.commit()
        conn.close()

        return render_template(
            "result.html",
            student_name=student_name,
            register_number=register_number,
            subject=subject,
            extracted_text=extracted_text,
            score=similarity_score,
            marks=marks
        )

    return render_template("upload.html")


@app.route("/history")
def history():
    if "user" not in session:
        flash("Please login first")
        return redirect(url_for("login"))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT student_name, register_number, subject, similarity_score, marks
        FROM evaluations
        ORDER BY id DESC
    """)
    rows = cur.fetchall()
    conn.close()

    return render_template("history.html", rows=rows)


@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("Logged out successfully")
    return redirect(url_for("login"))


@app.errorhandler(413)
def too_large(error):
    flash("File is too large. Maximum size is 16 MB.")
    return redirect(url_for("upload"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)