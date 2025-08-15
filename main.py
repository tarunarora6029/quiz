from flask import Flask,request,render_template,redirect,url_for,session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text
from datetime import datetime
import os
currentdir=os.path.dirname(__file__)
app=Flask(__name__)
app.secret_key=os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI']="sqlite:///"+os.path.join(currentdir,"quizmaster.sqlite3")
db=SQLAlchemy(app)

class User(db.Model):
    username = db.Column(db.String(30), primary_key=True)
    password = db.Column(db.String(30), nullable=False)
    name = db.Column(db.String(30), nullable=False)

class Quiz(db.Model):
    quiz = db.Column(db.String(20), primary_key=True)
    subject = db.Column(db.String(20), nullable=False)
    chapter = db.Column(db.String(20), nullable=False)
    deadline = db.Column(db.Date, nullable=False)

class Question(db.Model):
    qid = db.Column(db.Integer, primary_key=True)
    quiz = db.Column(db.String(20), db.ForeignKey("quiz.quiz"), nullable=False)
    question = db.Column(db.String(50), nullable=False)
    option1 = db.Column(db.String(50), nullable=False)
    option2 = db.Column(db.String(50), nullable=False)
    option3 = db.Column(db.String(50), nullable=False)
    option4 = db.Column(db.String(50), nullable=False)
    correct_answer = db.Column(db.Integer, nullable=False)

class Scores(db.Model):
    scoreid = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), db.ForeignKey("user.username"), nullable=False)
    quiz = db.Column(db.String(20), db.ForeignKey("quiz.quiz"), nullable=False)
    time = db.Column(db.DateTime, default=db.func.current_timestamp())
    score = db.Column(db.Integer, nullable=False)

with app.app_context():
    db.create_all()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods=["POST"])
def login():
    session.pop('username', None)
    username = request.form["username"]
    password = request.form["password"]
    if username == "admin":
        if password == "admin":
            return redirect(url_for('admindashboard'))
    user = User.query.filter_by(username=username, password=password).first()
    if user:
        session["username"] = username
        return redirect(url_for('userdashboard'))
    else:
        return render_template('index.html')

@app.route("/register", methods=["POST"])
def register():
    name = request.form["name"]
    username = request.form["username"]
    password = request.form["password"]
    if User.query.filter_by(username=username).first():
        return render_template('index.html')
    new_user = User(name=name, username=username, password=password)
    db.session.add(new_user)
    db.session.commit()
    return render_template('index.html')

@app.route("/admindashboard", methods=["GET", "POST"])
def admindashboard():
    if request.method == "POST":
        quiz = request.form["quiz"]
        subject = request.form["subject"]
        chapter = request.form["chapter"]
        deadline = request.form["deadline"]
        deadline = datetime.strptime(deadline, "%Y-%m-%d").date()
        new_quiz = Quiz(quiz=quiz, subject=subject, chapter=chapter, deadline=deadline)
        db.session.add(new_quiz)
        db.session.commit()
        return redirect(url_for("admindashboard"))
    quizzes = Quiz.query.all()
    return render_template("admindashboard.html", quizzes=quizzes)

@app.route('/quiz/<string:quiz>')
def view_quiz(quiz):
    quiz_details = Quiz.query.filter_by(quiz=quiz).first()
    questions = Question.query.filter_by(quiz=quiz).all()
    if quiz_details:
        return render_template('view_quiz.html', quiz=quiz_details, questions=questions )
    else:
        return redirect(url_for('admindashboard'))

@app.route('/delete_quiz/<string:quiz>')
def delete_quiz(quiz):
    quiz_to_delete = Quiz.query.filter_by(quiz=quiz).first()
    if quiz_to_delete:
        questions = Question.query.filter_by(quiz=quiz).all()
        for question in questions:
            db.session.delete(question)
        score = Scores.query.filter_by(quiz=quiz).all()
        for s in score:
            db.session.delete(s)
        db.session.delete(quiz_to_delete)
        db.session.commit()
        return redirect(url_for('admindashboard'))

@app.route('/quiz/<string:quiz>/edit', methods=['POST'])
def edit_quiz(quiz):
    quiz_details = Quiz.query.filter_by(quiz=quiz).first()
    if quiz_details:
        quiz_details.subject = request.form['subject']
        quiz_details.chapter = request.form['chapter']
        quiz_details.deadline = datetime.strptime(request.form['deadline'], '%Y-%m-%d')
        db.session.commit()
    return redirect(url_for('view_quiz', quiz=quiz))

@app.route('/quiz/<string:quiz>/add_question', methods=['POST'])
def add_question(quiz):
    question_text = request.form['question']
    option1 = request.form['option1']
    option2 = request.form['option2']
    option3 = request.form['option3']
    option4 = request.form['option4']
    correct_answer = int(request.form['correct_answer'])

    new_question = Question(
        quiz=quiz,
        question=question_text,
        option1=option1,
        option2=option2,
        option3=option3,
        option4=option4,
        correct_answer=correct_answer
    )
    db.session.add(new_question)
    db.session.commit()
    return redirect(url_for('view_quiz', quiz=quiz))

@app.route('/edit_question/<int:qid>', methods=['POST'])
def edit_question(qid):
    question = Question.query.filter_by(qid=qid).first()
    if question:
        question.question = request.form['question']
        question.option1 = request.form['option1']
        question.option2 = request.form['option2']
        question.option3 = request.form['option3']
        question.option4 = request.form['option4']
        question.correct_answer = int(request.form['correct_answer'])
        db.session.commit()
    return redirect(url_for('view_quiz', quiz=question.quiz))

@app.route('/question/<int:qid>/delete')
def delete_question(qid):
    question = Question.query.get(qid)
    if question:
        quiz = question.quiz
        db.session.delete(question)
        db.session.commit()
        return redirect(url_for('view_quiz', quiz=quiz))
    else:
        return redirect(url_for('view_quiz'))

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '').strip()
    results = []
    if query:
        quizzes = Quiz.query.filter(
            Quiz.quiz.ilike(f"%{query}%") |
            Quiz.subject.ilike(f"%{query}%") |
            Quiz.chapter.ilike(f"%{query}%")
        ).all()
        users = User.query.filter(User.username.ilike(f"%{query}%")).all()
        results = quizzes + users
    return render_template('search.html', results=results)

@app.route('/details')
def details():
    scores = Scores.query.order_by(Scores.time.desc()).all()
    total_users = User.query.count()
    total_quizzes = Quiz.query.count()
    avg_score = db.session.query(db.func.avg(Scores.score)).scalar()
    avg_score = round(avg_score, 2) if avg_score else 0
    return render_template('details.html', scores=scores, total_users=total_users, total_quizzes=total_quizzes,
                           avg_score=avg_score)

@app.route('/userdashboard')
def userdashboard():
    if 'username' not in session:
        return redirect(url_for('home'))
    quizzes = Quiz.query.all()
    return render_template('userdashboard.html', quizzes=quizzes, user= session["username"])

@app.route('/attempt_quiz/<string:quiz>')
def attempt_quiz(quiz):
    questions = Question.query.filter_by(quiz=quiz).all()
    if not questions:
        return redirect(url_for('userdashboard'))
    return render_template('attempt_quiz.html', questions=questions, quiz=quiz)

@app.route('/submit_quiz/<string:quiz>', methods=['POST'])
def submit_quiz(quiz):
    if 'username' not in session:
        return redirect(url_for('home'))
    questions = Question.query.filter_by(quiz=quiz).all()
    score = 0
    for question in questions:
        selected_answer = request.form.get(f"q{question.qid}")
        if selected_answer and int(selected_answer) == question.correct_answer:
            score += 1
    new_score = Scores(username=session["username"], quiz=quiz, time=datetime.utcnow(),score=score)
    db.session.add(new_score)
    db.session.commit()
    return redirect(url_for('userdashboard', username=session["username"]))

@app.route('/user_scores/<string:username>')
def user_scores(username):
    if 'username' not in session:
        return redirect(url_for('home'))
    scores = db.session.query(
        Scores.score, Scores.time,
        Quiz.quiz, Quiz.subject, Quiz.chapter
    ).join(Quiz, Scores.quiz == Quiz.quiz) \
     .filter(Scores.username == username) \
     .order_by(Scores.time.desc()).all()
    return render_template('user_scores.html', scores=scores)

if __name__ == "__main__":
    app.run(debug=True)

