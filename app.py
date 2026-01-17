from flask import Flask, blueprints, request, render_template, session, url_for, redirect, flash, send_file
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
app.config['JSONED_TASKS'] = "/static/json/"


def isLoggedin():
    return 'id' not in session


def isAdministrator():
    return not DBoperations.isAdmin(session['id'])


"""
if isAdministrator():
    render_template('404.html')

"""


@app.route("/")
def mainpage():
    return render_template('main.html')


@app.errorhandler(404)
def page_not_found():
    return render_template('404.html'), 404


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
    if not isLoggedin():
        return redirect(url_for('account'))
    msg = ""
    if request.method == "POST" and "username" in request.form and "password" in request.form and "email" \
            in request.form:
        username = request.form.get("username")
        password = request.form.get("password")
        email = request.form.get("email")
        # password_hash = sha256(password.encode('utf-8')).hexdigest()
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

        if DBoperations.checkUserEmail(email) is not None:
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
    if isLoggedin():
        return redirect(url_for('login'))
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
    if isLoggedin():
        return redirect(url_for('login'))
    if isAdministrator():
        return render_template('404.html')
    return render_template('tasks.html',
                           tasklist=DBoperations.getTasks())


@app.route("/account")
def account():
    if isLoggedin():
        return redirect(url_for('login'))
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


def allowed_file(filename, allowed_extensions):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in allowed_extensions


@app.route('/upload_avatar', methods=['POST'])
def upload_avatar():
    if isLoggedin():
        return redirect(url_for('login'))
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

        if file and allowed_file(file.filename, ALLOWED_EXTENSIONS_FOR_PICS):
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


@app.route('/task/<taskid>', methods=['GET'])
def task(taskid):
    if isLoggedin():
        return redirect(url_for('login'))
    if isAdministrator():
        return render_template('404.html')
    taskInfo = DBoperations.getTask(taskid)
    task_name = taskInfo['name']
    subject = taskInfo['subject']
    complexity = taskInfo['complexity']
    theme = taskInfo['theme']

    text = json.loads(taskInfo[9])
    description = text['desc']
    answer = text['answer']
    hint = text['hint']
    return render_template('task.html',
                           task_name=task_name,
                           subject=subject,
                           complexity=complexity,
                           theme=theme,
                           description=description,
                           answer=answer,
                           taskid=taskid,
                           hint=hint)


@app.route('/update_task/<taskid>', methods=['GET', 'POST'])
def update_task(taskid):
    if isLoggedin():
        return redirect(url_for('login'))
    if isAdministrator():
        return render_template('404.html')
    task_name = request.form.get('task_name')
    subject = request.form.get('subject')
    complexity = request.form.get('complexity')
    theme = request.form.get('theme')
    description = request.form.get('description')
    answer = request.form.get('answer')
    actionDelete = request.form.get('actionDelete')
    hint = request.form.get('hint')
    if actionDelete == "True":
        DBoperations.deleteTask(taskid)
    else:
        taskid = taskid
        DBoperations.updateTask(taskid, task_name, subject, complexity, theme, description, answer, hint)
    return redirect(url_for('tasks'))


@app.route('/new_task')
def new_task():
    if isLoggedin():
        return redirect(url_for('login'))
    if isAdministrator():
        return render_template('404.html')
    return render_template('new_task.html')


@app.route('/post_new_task', methods=['POST', 'GET'])
def post_new_task():
    if isLoggedin():
        return redirect(url_for('login'))
    if isAdministrator():
        return render_template('404.html')
    task_name = request.form.get('task_name')
    subject = request.form.get('subject')
    complexity = request.form.get('complexity')
    theme = request.form.get('theme')
    description = request.form.get('description')
    answer = request.form.get('answer')
    hint = request.form.get('hint')
    DBoperations.addNewTask(task_name, subject, complexity, theme, description, answer, hint, session['id'])
    return redirect(url_for('tasks'))


@app.route('/choose_task')
def choose_task():
    if isLoggedin():
        return redirect(url_for('login'))
    user_id = session['id']
    tasklist = DBoperations.getTasks()
    tasklist_not_solved = []
    solved = []
    unsolved = []
    # /choose_task?subject=Math&theme=Quadratic_equals
    subject = request.args.get('subject', "")
    complexity = request.args.get('complexity', "")
    theme = request.args.get('theme', "")
    allowedData = DBoperations.taskFilter(subject, theme, complexity)
    for i in tasklist:
        if i[0] in allowedData:
            if not DBoperations.solvedTasksBy(user_id, i[0]):
                tasklist_not_solved.append(i)
            else:
                if DBoperations.howSolved(user_id, i[0]):
                    solved.append(i)
                else:
                    unsolved.append(i)
    subjects = DBoperations.listSubjects()

    return render_template('choose_task.html', tasklist=tasklist_not_solved, solved=solved, unsolved=unsolved,
                           subject=subject, subjects=subjects, complexity=complexity)


@app.route('/solve_task/<taskid>', methods=['GET', 'POST'])
def solve_task(taskid):
    if isLoggedin():
        return redirect(url_for('login'))
    msg = ""
    DBoperations.startSolving(session['id'], taskid)
    solvationStatus = ""
    trigger = DBoperations.isSolved(session['id'], taskid)
    taskInfo = DBoperations.getTask(taskid)
    print(taskInfo)
    task_name = taskInfo[4]
    complexity = taskInfo[2]
    theme = taskInfo[3]
    hint_trigger = request.args.get('hint_trigger', False)
    if hint_trigger:
        DBoperations.setHintStatus(taskid, session['id'])
    text = json.loads(taskInfo[9])
    description = text['desc']
    hint = text['hint']
    right_answer = DBoperations.getSolvation(taskid)
    if request.method == "GET":
        return render_template('solve_task.html',
                               taskid=taskid,
                               task_name=task_name,
                               complexity=complexity,
                               theme=theme,
                               description=description,
                               hint=hint,
                               hint_trigger=hint_trigger,
                               trigger=trigger,
                               solvationStatus=solvationStatus
                               )
    if request.method == "POST":
        sent_answer = request.form.get('answer')

        if sent_answer == "" or sent_answer == " ":
            msg = "Поле ответа не может быть пустым!"
        else:
            DBoperations.setSolvationTime(taskid, session['id'])
            if right_answer == sent_answer:
                msg = "Задание решено верно!"
                DBoperations.setSolvation(taskid, session['id'], True)
            else:
                DBoperations.setSolvation(taskid, session['id'], False)
                msg = f"Задание решено неверно! Правильный ответ: {right_answer}. Ваш ответ: {sent_answer}"
        try:
            if DBoperations.howSolved(session['id'], taskid):
                solvationStatus = f"<div class='solvedRight'>Задание решено верно, ваш ответ: {right_answer}</div>"
            else:
                solvationStatus = f"<div class='solvedBad'>Задание решено неверно, правильный ответ: {right_answer}</div>"
        except TypeError:
            pass
        return render_template('solve_task.html',
                               taskid=taskid,
                               task_name=task_name,
                               complexity=complexity,
                               theme=theme,
                               description=description,
                               hint=hint,
                               hint_trigger=hint_trigger,
                               msg=msg,
                               sent_answer=sent_answer,
                               trigger=trigger,
                               solvationStatus=solvationStatus
                               )


@app.route('/download/<taskid>', methods=['GET', 'POST'])
def download(taskid):
    DBoperations.exportToJSON(taskid)
    path = f"static/json/file_{taskid}.json"
    print(path)
    return send_file(path, as_attachment=True)


@app.route('/import_task', methods=['POST'])
def import_task():
    if isLoggedin():
        return redirect(url_for('login'))
    if isAdministrator():
        return render_template('404.html')
    print("func")
    try:
        if 'file' not in request.files:
            flash('Не могу прочитать файл')
            return redirect(url_for('tasks'))

        file = request.files['file']
        if file.filename == '':
            flash('Нет выбранного файла')
            return redirect(url_for('tasks'))

        if file and allowed_file(file.filename, {'json'}):
            file_content = file.read().decode('utf-8')
            DBoperations.importFromJSON(session['id'], file_content)
            flash('Задача успешно загружена!')

            return redirect(url_for('tasks'))
        else:
            flash('Недопустимый формат файла. Разрешены: json')
            return redirect(url_for('tasks'))
    except Exception as e:
        print(f"{e} - Error!")
        flash('Произошла неизвестная ошибка')
        return redirect(url_for('tasks'))


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
