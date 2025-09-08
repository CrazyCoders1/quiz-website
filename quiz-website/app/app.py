from flask import Flask, render_template, request, jsonify, redirect, url_for
import mysql.connector
import random

app = Flask(__name__)

# MySQL Connection
db = mysql.connector.connect(
    host="sql303.infinityfree.com",
    user="if0_39895407",
    password="XV2TDjmrp1GJl3l",
    database="if0_39895407_quiz_db"
)
cursor = db.cursor(dictionary=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/practice')
def practice():
    cursor.execute("SELECT * FROM questions")
    questions = cursor.fetchall()
    return render_template('practice.html', questions=questions)

@app.route('/create_challenge', methods=['GET','POST'])
def create_challenge():
    if request.method == 'POST':
        username = request.form['username']
        num_questions = int(request.form['num_questions'])
        difficulty = request.form['difficulty']
        challenge_code = ''.join(random.choices('ABCDEFGHJKLMNPQRSTUVWXYZ123456789', k=6))
        cursor.execute(
            "INSERT INTO challenges (challenge_code, created_by, num_questions, difficulty) VALUES (%s,%s,%s,%s)",
            (challenge_code, username, num_questions, difficulty)
        )
        db.commit()
        return render_template('join_challenge.html', code=challenge_code)
    return render_template('create_challenge.html')

@app.route('/join_challenge', methods=['GET','POST'])
def join_challenge():
    if request.method=='POST':
        challenge_code = request.form['challenge_code']
        return redirect(url_for('challenge_quiz', code=challenge_code))
    return render_template('join_challenge.html')

@app.route('/challenge/<code>')
def challenge_quiz(code):
    cursor.execute("SELECT * FROM challenges WHERE challenge_code=%s",(code,))
    challenge = cursor.fetchone()
    if not challenge:
        return "Invalid Challenge Code"
    num_questions = challenge['num_questions']
    difficulty = challenge['difficulty']
    if difficulty=='Mixed':
        cursor.execute("SELECT * FROM questions WHERE exam_type='Easy'")
        easy_qs = cursor.fetchall()
        cursor.execute("SELECT * FROM questions WHERE exam_type='Tough'")
        tough_qs = cursor.fetchall()
        selected_questions = random.sample(easy_qs, int(num_questions*0.6)) + \
                             random.sample(tough_qs, int(num_questions*0.4))
    else:
        cursor.execute("SELECT * FROM questions WHERE exam_type=%s",(difficulty,))
        all_qs = cursor.fetchall()
        selected_questions = random.sample(all_qs,min(num_questions,len(all_qs)))
    random.shuffle(selected_questions)
    return render_template('practice.html', questions=selected_questions, challenge_code=code)

@app.route('/submit_score', methods=['POST'])
def submit_score():
    data = request.json
    username = data['username']
    challenge_code = data['challenge_code']
    score = int(data['score'])
    cursor.execute("SELECT id FROM challenges WHERE challenge_code=%s",(challenge_code,))
    challenge = cursor.fetchone()
    if not challenge:
        return jsonify({'status':'error'})
    challenge_id = challenge['id']
    cursor.execute("""
        INSERT INTO challenge_scores (challenge_id, username, score)
        VALUES (%s,%s,%s)
        ON DUPLICATE KEY UPDATE score=VALUES(score)
    """,(challenge_id,username,score))
    db.commit()
    cursor.execute("""
        INSERT INTO users (username, total_score)
        VALUES (%s,%s)
        ON DUPLICATE KEY UPDATE total_score=total_score+%s
    """,(username,score,score))
    db.commit()
    return jsonify({'status':'success'})

@app.route('/leaderboard')
def leaderboard():
    cursor.execute("SELECT username,total_score FROM users ORDER BY total_score DESC")
    users = cursor.fetchall()
    return render_template('leaderboard.html', users=users)

if __name__=="__main__":
    app.run(debug=True)
