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

@app.route('/create_challenge', methods=['GET', 'POST'])
def create_challenge():
    if request.method == 'POST':
        challenge_name = request.form['challenge_name']
        duration = int(request.form['duration'])
        difficulty = request.form['difficulty']
        num_questions = int(request.form['num_questions'])
        
        conn = get_conn()
        cur = conn.cursor()
        
        if difficulty == 'medium':
            # 60% easy, 40% hard
            easy_count = int(num_questions * 0.6)
            hard_count = num_questions - easy_count
            cur.execute(f"SELECT * FROM questions WHERE difficulty='easy' ORDER BY RANDOM() LIMIT {easy_count}")
            easy_qs = cur.fetchall()
            cur.execute(f"SELECT * FROM questions WHERE difficulty='hard' ORDER BY RANDOM() LIMIT {hard_count}")
            hard_qs = cur.fetchall()
            questions = easy_qs + hard_qs
        else:
            cur.execute(f"SELECT * FROM questions WHERE difficulty=%s ORDER BY RANDOM() LIMIT %s", (difficulty, num_questions))
            questions = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return render_template('createChallenge.html', questions=questions, challenge_name=challenge_name, duration=duration)
    
    return render_template('createChallenge.html')

@app.route('/join_challenge')
def join_challenge():
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
        
        if ADMINS.get(username) == password:
            flash('Logged in as admin', 'success')
            return redirect(url_for('upload_pdf'))
        else:
            flash('Invalid credentials', 'danger')
    
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
