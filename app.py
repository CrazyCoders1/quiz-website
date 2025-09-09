from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from flask_cors import CORS
import os
import fitz  # PyMuPDF for PDF → images
from PIL import Image
import psycopg2
import random

app = Flask(__name__)
CORS(app)
app.secret_key = 'sparkyy2027'

# Supabase DB URL (stored as environment variable in Render)
DATABASE_URL = os.environ.get('DATABASE_URL')

# Folder paths
UPLOAD_FOLDER = 'data'
EASY_FOLDER = 'static/questions/easy'
HARD_FOLDER = 'static/questions/hard'
os.makedirs(EASY_FOLDER, exist_ok=True)
os.makedirs(HARD_FOLDER, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Admin credentials (simple)
ADMINS = {'admin': 'password123'}
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "password123")

# Connect to Supabase DB
def get_conn():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

# ------------------- ROUTES -------------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/practice')
def practice():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM questions ORDER BY RANDOM() LIMIT 10;")
    questions = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('practice.html', questions=questions)

@app.route('/createChallenge', methods=['GET', 'POST'])
def createChallenge():
    if request.method == 'POST':
        challenge_name = request.form['challenge_name']
        num_questions = int(request.form['num_questions'])
        difficulty = request.form['difficulty']

        conn = get_conn()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO challenges (name, num_questions, difficulty) VALUES (%s, %s, %s) RETURNING id",
            (challenge_name, num_questions, difficulty)
        )
        challenge_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()

        return redirect(f'/joinChallenge/{challenge_id}')  # redirect after create

    return render_template('createChallenge.html')

@app.route('/joinChallenge')
def joinChallenge():
    return render_template('joinChallenge.html')

@app.route('/leaderboard')
def leaderboard():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT username, score FROM leaderboard ORDER BY score DESC LIMIT 10;")
    leaders = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('leaderboard.html', leaders=leaders)

# ------------------- ADMIN -------------------

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == ADMIN_USER and password == ADMIN_PASS:
            return redirect('/upload_pdf')
        else:
            return "Invalid credentials", 401

    return render_template('admin.html')
    
@app.route("/submit_score", methods=["POST"])
def submit_score():
    data = request.get_json()
    username = data.get("username")
    score = data.get("score")

    cur = conn.cursor()
    cur.execute("INSERT INTO leaderboard (username, score) VALUES (%s, %s)", (username, score))
    conn.commit()
    cur.close()

    return jsonify({"message": "Score saved!"}), 200

@app.route("/upload_pdf", methods=["POST"])
def upload_pdf():
    try:
        file = request.files["file"]
        if not file:
            return jsonify({"error": "No file uploaded"}), 400

        # Read file into memory
        pdf_bytes = file.read()

        import fitz  # PyMuPDF
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")

        text = ""
        for page in doc:
            text += page.get_text()

        # Store in DB
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("INSERT INTO uploads (content) VALUES (%s)", (text,))
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"message": "PDF uploaded and processed successfully!"})

    except Exception as e:
        import traceback
        traceback.print_exc()  # prints full error in Render logs
        return jsonify({"error": str(e)}), 500

# ------------------- RUN -------------------

if __name__ == '__main__':
    app.run(debug=True)
