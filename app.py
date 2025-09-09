# app.py
import os
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import psycopg2
import psycopg2.extras
from urllib.parse import urlparse

app = Flask(__name__)
CORS(app)  # allow requests from your frontend domain

# Use DATABASE_URL environment variable (from Supabase)
DATABASE_URL = os.getenv("DATABASE_URL")

def get_conn():
    # psycopg2 will accept the DATABASE_URL string directly
    conn = psycopg2.connect(DATABASE_URL, sslmode="require")
    return conn

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/practice")
def practice():
    return render_template("practice.html")

# Example: fetch questions for practice (easy/tough/mixed)
@app.route("/get_quiz", methods=["POST"])
def get_quiz():
    data = request.json
    num = int(data.get("num", 10))
    difficulty = data.get("difficulty", "Easy")  # "Easy","Tough","Mixed"
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    if difficulty == "Mixed":
        num_easy = int(num * 0.6)
        num_tough = num - num_easy
        cur.execute("SELECT * FROM questions WHERE exam_type='Easy' ORDER BY random() LIMIT %s", (num_easy,))
        easy = cur.fetchall()
        cur.execute("SELECT * FROM questions WHERE exam_type='Tough' ORDER BY random() LIMIT %s", (num_tough,))
        tough = cur.fetchall()
        qs = easy + tough
    else:
        cur.execute("SELECT * FROM questions WHERE exam_type=%s ORDER BY random() LIMIT %s", (difficulty, num))
        qs = cur.fetchall()

    cur.close(); conn.close()
    # Return JSON (Flask will convert)
    return jsonify(qs)

# Submit score (challenge or practice)
@app.route("/submit_score", methods=["POST"])
def submit_score():
    data = request.json
    username = data.get("username")
    score = int(data.get("score", 0))
    challenge_code = data.get("challenge_code")  # optional

    conn = get_conn()
    cur = conn.cursor()

    # Update global users total_score
    cur.execute("""
        INSERT INTO users (username, total_score)
        VALUES (%s, %s)
        ON CONFLICT (username) DO UPDATE
          SET total_score = users.total_score + EXCLUDED.total_score
    """, (username, score))

    # If challenge_code provided, map to challenge_id and upsert into challenge_scores
    if challenge_code:
        cur.execute("SELECT id FROM challenges WHERE challenge_code = %s", (challenge_code,))
        row = cur.fetchone()
        if row:
            challenge_id = row[0]
            # insert or update
            cur.execute("""
                INSERT INTO challenge_scores (challenge_id, username, score)
                VALUES (%s, %s, %s)
                ON CONFLICT (challenge_id, username) DO UPDATE
                SET score = EXCLUDED.score
            """, (challenge_id, username, score))
    conn.commit()
    cur.close(); conn.close()
    return jsonify({"status": "ok"})

# Leaderboard
@app.route("/leaderboard")
def leaderboard():
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT username, total_score FROM users ORDER BY total_score DESC LIMIT 50")
    rows = cur.fetchall()
    cur.close(); conn.close()
    return jsonify(rows)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
