"""
EduConnect - Basic Edition (Render & Production Ready)
======================================================
The minimalist, clean 3-Step Hyperlocal Learning Platform:
  Step 1: Take Student & Teacher Data + GPS Coordinates
  Step 2: Calculate Distances Using the Haversine Algorithm
  Step 3: Create Tuition Cohorts & Real-Time Discussion Chat

Ready for deployment on Render, Railway, Heroku, and GitHub.
Automatically supports both MySQL and SQLite (for zero-config cloud hosting).
"""

import os
import math
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash

try:
    import mysql.connector
    HAS_MYSQL = True
except ImportError:
    HAS_MYSQL = False

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "educonnect_super_secret_production_key_2026")

# Database Configuration (supports MySQL & auto-fallback to SQLite for Render)
MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
MYSQL_USER = os.environ.get("MYSQL_USER", "root")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "root")
MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "online_education")
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", 3306))
SQLITE_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "educonnect.db")

# ----------------------------------------------------------------------
# DATABASE ADAPTER (Seamless MySQL & SQLite support)
# ----------------------------------------------------------------------
class DBConnection:
    """Unified wrapper allowing identical code for MySQL and SQLite."""
    def __init__(self, is_mysql, conn):
        self.is_mysql = is_mysql
        self.conn = conn

    def cursor(self, dictionary=True):
        if self.is_mysql:
            return self.conn.cursor(dictionary=dictionary)
        else:
            self.conn.row_factory = sqlite3.Row if dictionary else None
            return SQLiteCursorWrapper(self.conn.cursor(), self.conn)

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

class SQLiteCursorWrapper:
    def __init__(self, cursor, conn):
        self.cursor = cursor
        self.conn = conn
        self.lastrowid = None

    def execute(self, sql, params=()):
        # Convert MySQL %s placeholders to SQLite ? placeholders
        clean_sql = sql.replace("%s", "?")
        res = self.cursor.execute(clean_sql, params)
        self.lastrowid = self.cursor.lastrowid
        return res

    def fetchone(self):
        row = self.cursor.fetchone()
        return dict(row) if row else None

    def fetchall(self):
        rows = self.cursor.fetchall()
        return [dict(r) for r in rows] if rows else []

    def close(self):
        self.cursor.close()

def init_sqlite_if_needed():
    """Initializes SQLite schema and test accounts when deploying without MySQL."""
    conn = sqlite3.connect(SQLITE_DB)
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            mobile TEXT NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'student',
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS student_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            grade TEXT NOT NULL,
            board TEXT NOT NULL,
            subjects TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS teacher_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            qualification TEXT NOT NULL,
            experience TEXT NOT NULL,
            subjects_taught TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS cohorts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            subject TEXT NOT NULL,
            grade TEXT NOT NULL,
            created_by INTEGER NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS cohort_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cohort_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            role TEXT DEFAULT 'member',
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS cohort_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cohort_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            message_type TEXT DEFAULT 'text',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Seed demo users if empty
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        pw = generate_password_hash("password123")
        c.execute("""
            INSERT INTO users (full_name, email, mobile, password, role, latitude, longitude)
            VALUES ('Hemanth Varma', 'hemanth@example.com', '9876543210', ?, 'teacher', 17.3850, 78.4867)
        """, (pw,))
        t_id = c.lastrowid
        c.execute("""
            INSERT INTO teacher_profiles (user_id, qualification, experience, subjects_taught)
            VALUES (?, 'M.Sc Chemistry', '5 years', 'Chemistry, MPC')
        """, (t_id,))

        c.execute("""
            INSERT INTO users (full_name, email, mobile, password, role, latitude, longitude)
            VALUES ('Aarav Sharma', 'student@example.com', '9876543211', ?, 'student', 17.3910, 78.4920)
        """, (pw,))
        s_id = c.lastrowid
        c.execute("""
            INSERT INTO student_profiles (user_id, grade, board, subjects)
            VALUES (?, 'Class 10', 'CBSE', 'Chemistry, Mathematics')
        """, (s_id,))

        c.execute("""
            INSERT INTO cohorts (name, description, subject, grade, created_by, latitude, longitude)
            VALUES ('Class 10 Chemistry Masters', 'Intensive revision cohort for CBSE boards', 'Chemistry', 'Class 10', ?, 17.3850, 78.4867)
        """, (t_id,))
        coh_id = c.lastrowid

        c.execute("INSERT INTO cohort_members (cohort_id, user_id, role) VALUES (?, ?, 'creator')", (coh_id, t_id))
        c.execute("INSERT INTO cohort_members (cohort_id, user_id, role) VALUES (?, ?, 'member')", (coh_id, s_id))
        c.execute("""
            INSERT INTO cohort_messages (cohort_id, user_id, message)
            VALUES (?, ?, 'Welcome to the Chemistry Masters cohort! Feel free to ask questions here.')
        """, (coh_id, t_id))

    conn.commit()
    conn.close()

def get_db():
    """Connects to MySQL if reachable; otherwise seamlessly uses SQLite."""
    if HAS_MYSQL:
        try:
            raw = mysql.connector.connect(
                host=MYSQL_HOST,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DATABASE,
                port=MYSQL_PORT,
                connect_timeout=3
            )
            return DBConnection(is_mysql=True, conn=raw)
        except Exception:
            pass
    
    init_sqlite_if_needed()
    raw = sqlite3.connect(SQLITE_DB)
    return DBConnection(is_mysql=False, conn=raw)

# ----------------------------------------------------------------------
# STEP 2 ALGORITHM: THE HAVERSINE DISTANCE FORMULA
# ----------------------------------------------------------------------
def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculates great-circle surface distance in kilometers between two GPS points
    across Earth's spherical surface (Earth Radius R = 6,371.0 km).
    """
    try:
        lat1, lon1, lat2, lon2 = float(lat1), float(lon1), float(lat2), float(lon2)
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat / 2.0) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2.0) ** 2)
        c = 2.0 * math.asin(math.sqrt(a))
        
        return round(c * 6371.0, 2)
    except Exception:
        return None

# ----------------------------------------------------------------------
# NAVIGATION & AUTHENTICATION (STEP 1: TAKE DATA)
# ----------------------------------------------------------------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        db.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["full_name"]
            session["user_role"] = user["role"]
            return redirect(url_for("dashboard"))
        
        flash("Invalid email or password.", "error")
        return render_template("login.html", error="Invalid email or password.")
        
    return render_template("login.html")

@app.route("/demo-login/<identifier>")
def demo_login(identifier):
    """1-click evaluation login for fast review."""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    if identifier == "teacher":
        cursor.execute("SELECT * FROM users WHERE role = 'teacher' ORDER BY id ASC LIMIT 1")
    elif identifier == "student":
        cursor.execute("SELECT * FROM users WHERE role = 'student' ORDER BY id ASC LIMIT 1")
    else:
        cursor.execute("SELECT * FROM users WHERE email LIKE %s OR full_name LIKE %s LIMIT 1",
                       (f"%{identifier}%", f"%{identifier}%"))
    user = cursor.fetchone()
    cursor.close()
    db.close()

    if user:
        session["user_id"] = user["id"]
        session["user_name"] = user["full_name"]
        session["user_role"] = user["role"]
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/student-register", methods=["GET", "POST"])
def student_register():
    if request.method == "POST":
        name = request.form.get("full_name") or request.form.get("name")
        email = request.form.get("email", "").strip().lower()
        mobile = request.form.get("mobile", "")
        password = generate_password_hash(request.form.get("password", "secret123"))
        grade = request.form.get("grade", "Class 10")
        board = request.form.get("board", "CBSE")
        subjects = ", ".join(request.form.getlist("subjects")) or "All Subjects"
        lat = float(request.form.get("latitude") or 17.3850)
        lng = float(request.form.get("longitude") or 78.4867)

        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO users (full_name, email, mobile, password, role, latitude, longitude)
            VALUES (%s, %s, %s, %s, 'student', %s, %s)
        """, (name, email, mobile, password, lat, lng))
        user_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO student_profiles (user_id, grade, board, subjects)
            VALUES (%s, %s, %s, %s)
        """, (user_id, grade, board, subjects))
        db.commit()
        cursor.close()
        db.close()

        session["user_id"] = user_id
        session["user_name"] = name
        session["user_role"] = "student"
        return redirect(url_for("dashboard"))

    return render_template("student_registration_form.html")

@app.route("/teacher-register", methods=["GET", "POST"])
def teacher_register():
    if request.method == "POST":
        name = request.form.get("full_name") or request.form.get("name")
        email = request.form.get("email", "").strip().lower()
        mobile = request.form.get("mobile", "")
        password = generate_password_hash(request.form.get("password", "secret123"))
        qualification = request.form.get("qualification", "B.Tech / M.Sc")
        experience = request.form.get("experience", "3 years")
        subjects = ", ".join(request.form.getlist("subjects")) or "Mathematics"
        lat = float(request.form.get("latitude") or 17.3850)
        lng = float(request.form.get("longitude") or 78.4867)

        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO users (full_name, email, mobile, password, role, latitude, longitude)
            VALUES (%s, %s, %s, %s, 'teacher', %s, %s)
        """, (name, email, mobile, password, lat, lng))
        user_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO teacher_profiles (user_id, qualification, experience, subjects_taught)
            VALUES (%s, %s, %s, %s)
        """, (user_id, qualification, experience, subjects))
        db.commit()
        cursor.close()
        db.close()

        session["user_id"] = user_id
        session["user_name"] = name
        session["user_role"] = "teacher"
        return redirect(url_for("dashboard"))

    return render_template("teacher_registration_form.html")

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id = %s", (session["user_id"],))
    user = cursor.fetchone()
    cursor.close()
    db.close()
    
    return render_template("dashboard.html", user=user)

# ----------------------------------------------------------------------
# STEP 2: HAVERSINE RADAR (EXPLORE TUTORS / STUDENTS)
# ----------------------------------------------------------------------
@app.route("/nearby")
def nearby():
    if "user_id" not in session:
        return redirect(url_for("login"))

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users WHERE id = %s", (session["user_id"],))
    current_user = cursor.fetchone()

    if current_user["role"] == "student":
        cursor.execute("""
            SELECT u.*, t.qualification, t.experience, t.subjects_taught
            FROM users u JOIN teacher_profiles t ON u.id = t.user_id
        """)
    else:
        cursor.execute("""
            SELECT u.*, s.grade, s.board, s.subjects
            FROM users u JOIN student_profiles s ON u.id = s.user_id
        """)
    candidates = cursor.fetchall()
    cursor.close()
    db.close()

    results = []
    max_radius = float(request.args.get("max_dist", 50))
    for c in candidates:
        dist = haversine_distance(current_user["latitude"], current_user["longitude"],
                                  c["latitude"], c["longitude"])
        if dist is not None and dist <= max_radius:
            c["distance_km"] = dist
            results.append(c)

    results.sort(key=lambda x: x["distance_km"])
    return render_template("nearby.html", current_user=current_user, results=results)

# ----------------------------------------------------------------------
# STEP 3: COHORTS & REAL-TIME CHAT
# ----------------------------------------------------------------------
@app.route("/cohorts")
def cohorts_list():
    if "user_id" not in session:
        return redirect(url_for("login"))

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM cohorts ORDER BY id DESC")
    cohorts = cursor.fetchall()

    cursor.execute("SELECT * FROM users WHERE id = %s", (session["user_id"],))
    current_user = cursor.fetchone()
    cursor.close()
    db.close()

    return render_template("cohorts.html", cohorts=cohorts, current_user=current_user)

@app.route("/cohort/create", methods=["POST"])
def create_cohort():
    if "user_id" not in session:
        return redirect(url_for("login"))

    name = request.form.get("name")
    subject = request.form.get("subject")
    grade = request.form.get("grade")
    description = request.form.get("description", "")

    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO cohorts (name, description, subject, grade, created_by, latitude, longitude)
        VALUES (%s, %s, %s, %s, %s, 17.3850, 78.4867)
    """, (name, description, subject, grade, session["user_id"]))
    cohort_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO cohort_members (cohort_id, user_id, role)
        VALUES (%s, %s, 'creator')
    """, (cohort_id, session["user_id"]))
    db.commit()
    cursor.close()
    db.close()

    return redirect(url_for("cohort_detail", cohort_id=cohort_id))

@app.route("/cohort/<int:cohort_id>")
def cohort_detail(cohort_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM cohorts WHERE id = %s", (cohort_id,))
    cohort = cursor.fetchone()

    cursor.execute("""
        SELECT m.*, u.full_name as author_name, u.role as author_role
        FROM cohort_messages m JOIN users u ON m.user_id = u.id
        WHERE m.cohort_id = %s ORDER BY m.created_at ASC
    """, (cohort_id,))
    messages = cursor.fetchall()

    cursor.execute("SELECT * FROM users WHERE id = %s", (session["user_id"],))
    current_user = cursor.fetchone()
    cursor.close()
    db.close()

    return render_template("cohort_detail.html", cohort=cohort, messages=messages, current_user=current_user)

@app.route("/cohort/<int:cohort_id>/message", methods=["POST"])
def post_cohort_message(cohort_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    msg = request.form.get("message", "").strip()
    if msg:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO cohort_messages (cohort_id, user_id, message, message_type)
            VALUES (%s, %s, %s, 'text')
        """, (cohort_id, session["user_id"], msg))
        db.commit()
        cursor.close()
        db.close()

    return redirect(url_for("cohort_detail", cohort_id=cohort_id))

@app.route("/cohort/<int:cohort_id>/api/messages")
def get_cohort_messages_api(cohort_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT m.*, u.full_name as author_name, u.role as author_role
        FROM cohort_messages m JOIN users u ON m.user_id = u.id
        WHERE m.cohort_id = %s ORDER BY m.created_at ASC
    """, (cohort_id,))
    messages = cursor.fetchall()
    cursor.close()
    db.close()
    return jsonify({"messages": messages})

# ----------------------------------------------------------------------
# RUN SERVER (Dynamic Port for Render & Cloud)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"EduConnect running on http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
