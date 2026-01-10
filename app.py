from flask import Flask, blueprints, request, render_template, session, url_for, redirect, flash
from hashlib import sha256
import bcrypt
import re
import DBoperations
from dotenv import load_dotenv
import os
import json
from pathlib import Path

ALLOWED_EXTENSIONS_FOR_PICS = {'png', 'jpg', 'jpeg'}
BASE_DIR = Path(__file__).parent
UPLOAD_FOLDER = BASE_DIR / 'static' / 'profile_pics'
app = Flask(__name__)
load_dotenv()
app.secret_key = os.getenv('SECRET_KEY')
DBoperations.init_db()
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024


@app.route("/")
def mainpage():
    return render_template('main.html')


@app.route("/login", methods=["GET", "POST"])
def login():
    msg = ""
    if request.method == "POST" and "username" in request.form and "password" in request.form:
        username = request.form.get("username")
        password = request.form.get("password")
        account = DBoperations.loginUser(username, password)
        if account:
            session['loggedin'] = True
            session['id'] = account[0]
            session['username'] = account[1]
            session['email'] = account[4]
            session['adm'] = DBoperations.isAdmin(account[0])
            profile_pic_path = f"static/profile_pics/pic_{session['id']}"
            if os.path.exists(profile_pic_path):
                session['profile_pic'] = f"/static/profile_pics/pic_{session['id']}"
            else:
                session['profile_pic'] = "/static/profile_pics/generic_profile_picture.jpg"
            return redirect(url_for('dashboard'))
        else:
            msg = "Аккаунта не существует или введен некорректный пароль!"
    return render_template('login.html', msg=msg)


@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    session.pop('email', None)
    return redirect(url_for('login'))


@app.route("/register", methods=["GET", "POST"])
def register():
    msg = ""
    if request.method == "POST" and "username" in request.form and "password" in request.form and "email" in request.form:
        username = request.form.get("username")
        password = request.form.get("password")
        email = request.form.get("email")
        #password_hash = sha256(password.encode('utf-8')).hexdigest()
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

        if DBoperations.checkUserEmail(email) != None:
            msg = "Данная почта уже зарегистрирована"
        elif not re.match(r"^[A-Za-z0-9_]+$", username):
            msg = "Запрещенные символы в имени. Разрешена латиница, цифры и _"
        elif DBoperations.checkUserName(username) != None:
            msg = "Данный никнейм уже используется!"
        elif not username or not email or not password:
            msg = "Пожалуйста, заполните все поля!"
        elif len(password) < 8:
            msg = "Пароль должен быть длиной 8 и более символов!"
        else:
            DBoperations.addNewUser(username, email, password_hash)
            return redirect(url_for('dashboard'))

    return render_template('register.html', msg=msg)


@app.route("/dashboard")
def dashboard():
    try:
        # Таблички
        scores = DBoperations.takeScorebyDays(session['id'])
        chart_data = []
        for date, score in scores:
            chart_data.append([date.strftime("%Y-%m-%d"), score])

        # Преобразуем в JSON строку
        chart_data = json.dumps(chart_data)

        return render_template('dashboard.html',
                               chart_data_json=chart_data,
                               username=session.get('username', 'Пользователь')
                               )
    except KeyError:
        return redirect(url_for('login'))

@app.route("/tasks")
def tasks():
    return render_template('tasks.html',
                           tasklist=DBoperations.getTasks())
@app.route("/account")
def account():
    # Фото профиля
    profile_pic_path = f"static/profile_pics/pic_{session['id']}"
    if not os.path.exists(profile_pic_path):
        print("not exists")
        profile_pic = "static/profile_pics/generic_profile_picture.jpg"
    else:
        profile_pic = f"static/profile_pics/pic_{session['id']}"
    return render_template('account.html',
                           profile_pic=profile_pic)

@app.context_processor
def inject_user_data():
    if 'loggedin' in session and session['loggedin']:
        return dict(
            loggedin=True,
            username=session.get('username'),
            profile_pic=session.get('profile_pic', f'/static/profile_pics/{session["id"]}.jpg'),
            user_id=session.get('id')
        )
    return dict(
        loggedin=False,
        profile_pic="/static/profile_pics/generic_profile_picture.jpg",
        username=None
    )


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS_FOR_PICS


@app.route('/upload_avatar', methods=['POST'])
def upload_avatar():
    print("func")
    try:
        user_id = session['id']

        if 'file' not in request.files:
            flash('Не могу прочитать файл')
            return redirect(url_for('dashboard'))

        file = request.files['file']
        if file.filename == '':
            flash('Нет выбранного файла')
            return redirect(url_for('dashboard'))

        if file and allowed_file(file.filename):
            if not os.path.exists(UPLOAD_FOLDER):
                os.makedirs(UPLOAD_FOLDER)

            print("There is no mistakes")
            filename = f"pic_{user_id}"
            filepath = os.path.join(UPLOAD_FOLDER, filename)

            file.save(filepath)
            flash('Аватар успешно обновлен!')

            return redirect(url_for('account'))
        else:
            flash('Недопустимый формат файла. Разрешены: png, jpg, jpeg')
            return redirect(url_for('account'))

    except Exception as e:
        print(f"Ошибка загрузки аватара: {e}")
        flash('Произошла ошибка при загрузке файла')
        return redirect(url_for('dashboard'))

@app.route('/admin_panel', methods=['GET', 'POST'])
def admin_panel():
    return render_template('admin_panel.html')

@app.route('/task/<taskid>', methods=['GET'])
def task(taskid):
    taskInfo = DBoperations.getTask(taskid)
    print(taskInfo)
    task_name = taskInfo[4]
    subject = taskInfo[1]
    complexity = taskInfo[2]
    theme = taskInfo[3]

    text = json.loads(taskInfo[9])
    print(text)
    description = text['desc']
    answer = text['answer']
    return render_template('task.html',
                           task_name=task_name,
                           subject=subject,
                           complexity=complexity,
                           theme=theme,
                           description=description,
                           answer=answer,
                           taskid=taskid)
@app.route('/update_task/<taskid>', methods=['GET', 'POST'])
def update_task(taskid):
    task_name = request.form.get('task_name')
    subject = request.form.get('subject')
    complexity = request.form.get('complexity')
    theme = request.form.get('theme')
    description = request.form.get('description')
    answer = request.form.get('answer')
    actionDelete = request.form.get('actionDelete')
    if actionDelete == "True":
        DBoperations.deleteTask(taskid)
    else:
        taskid = taskid
        DBoperations.updateTask(taskid, task_name, subject, complexity, theme, description, answer)
    return redirect(url_for('tasks'))

@app.route('/new_task')
def new_task():
    return render_template('new_task.html')

@app.route('/post_new_task', methods=['POST', 'GET'])
def post_new_task():
    task_name = request.form.get('task_name')
    subject = request.form.get('subject')
    complexity = request.form.get('complexity')
    theme = request.form.get('theme')
    description = request.form.get('description')
    answer = request.form.get('answer')
    DBoperations.addNewTask(task_name, subject, complexity, theme, description, answer)
    return redirect(url_for('tasks'))

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
