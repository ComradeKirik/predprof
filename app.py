from flask import Flask, blueprints, request, render_template, session, url_for, redirect, flash, send_file, \
    make_response, abort
from flask_socketio import SocketIO, send, emit, join_room, leave_room
import bcrypt
import re
import DBoperations
from dotenv import load_dotenv
import os
import json
from pathlib import Path
from io import StringIO

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
socketio = SocketIO(app)

users = {}


# Handle user messages
@socketio.on('message')
def handle_message(data):
    username = users.get(request.sid, "Anonymous")  # Get the user's name
    emit("message", f"{username}: {data}", broadcast=True)  # Send to everyone


# Handle disconnects
@socketio.on('disconnect')
def handle_disconnect():
    username = users.pop(request.sid, "Anonymous")
    emit("message", f"{username} left the chat", broadcast=True)


# @app.route('/route')
# def index():
#     return render_template('websocket.html')

# Handle new user joining
# @socketio.on('join')
# def handle_join(username):
#     users[request.sid] = username  # Store username by session ID
#     join_room(username)  # Each user gets their own "room"
#     emit("message", f"{username} joined the chat", room=username)

@socketio.on('request_reload')
def handle_request_reload(data):
    print("Получено событие перезагрузки, транслируем всем клиентам.")
    emit('reload_page', broadcast=True)  # Отправляем всем клиентам


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
    DBoperations.checkContestExpiration()
    DBoperations.checkContestStart()
    if isLoggedin():
        return redirect(url_for('login'))
    # Фото профиля
    profile_pic_path = f"static/profile_pics/pic_{session['id']}"
    if not os.path.exists(profile_pic_path):
        print("not exists")
        profile_pic = "static/profile_pics/generic_profile_picture.jpg"
    else:
        profile_pic = f"static/profile_pics/pic_{session['id']}"

    contests = DBoperations.takeContestsByUid(session['id'])
    print(contests)
    return render_template('account.html',
                           profile_pic=profile_pic, contests=contests)

@app.route('/delete-account', methods=['POST'])
def delete_account():
    username = request.form.get('confirm_username')
    password = request.form.get('confirm_password')
    account = DBoperations.loginUser(username, password)
    if account:
        DBoperations.deleteAccount(session['id'])
        return redirect(url_for('logout'))
    else:
        flash('Введен некорректный никнейм или пароль!')
        return redirect(url_for('account'))

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
    emit('message', 'update_task', broadcast=True, namespace="/")
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
    emit('message', 'post_new_task', broadcast=True, namespace="/")
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
    JSON_task = DBoperations.exportToJSON(taskid)
    # path = f"static/json/file_{taskid}.json"
    # print(path)
    # return send_file(path, as_attachment=True)
    with StringIO() as buffer:
        # forming a StringIO object
        buffer = StringIO()
        buffer.write(JSON_task)
        # forming a Response object with Headers to return from flask
        response = make_response(buffer.getvalue())
        response.headers['Content-Disposition'] = 'attachment; filename=task.json'
        response.mimetype = 'text/json'
        # return the Response object
        return response


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


@app.route('/contests')
def contest_list():
    DBoperations.checkContestExpiration()
    DBoperations.checkContestStart()
    if isLoggedin():
        return redirect(url_for('login'))
    contests = DBoperations.listContests()
    unexpired_contests = DBoperations.listUnexpiredContests()
    if not contests:
        return render_template('contest_list.html', contests=['Соревнования отсутствуют'])
    return render_template('contest_list.html', contests=unexpired_contests)


# Заявка на контест
@app.route('/applyToContest/<contid>')
def applyToContest(contid):
    if not DBoperations.isUserInContest(session['id'], contid):
        DBoperations.addUserToContest(session['id'], contid)
        flash('Вы успешно приняли вызов!')
    else:
        flash('Вы уже участник этого поединка!', 'error')
        return redirect(url_for('contest_list'))

    emit('message', 'applied_to_contest', broadcast=True, namespace="/")
    return redirect(url_for('contest_list'))


# Функция для генерации страницы с созданием соревнования
@app.route('/create_contest')
def create_contest():
    if isLoggedin():
        return redirect(url_for('login'))
    subjects = DBoperations.listSubjects()
    return render_template('create_contest.html', subjects=subjects)


# Функция для обработки создания соревнования
@app.route("/post_new_contest", methods=['POST'])
def post_new_contest():
    if isLoggedin():
        return redirect(url_for('login'))
    try:
        data = {
            'subject': request.form.get('subject', '').strip(),
            'complexity': request.form.get('complexity'),
            'started_at': request.form.get('started_at'),
            'ending_at': request.form.get('ending_at'),
            'user_2': request.form.get('user_2') or None,
            'u1_accepted': True
        }

        # Получаем ID текущего пользователя из сессии
        user1_id = session.get('id')
        if not user1_id:
            flash('Пользователь не авторизован', 'error')
            return redirect(url_for('login'))

        contest_id = DBoperations.createNewContest(data, user1_id)

        flash(f'Соревнование #{contest_id} успешно создано!', 'success')
        emit('message', 'post_new_contest', broadcast=True, namespace="/")
        return redirect(url_for('contest_list'))

    except ValueError as e:
        flash(f'Ошибка в данных: {str(e)}', 'error')
        return redirect(url_for('create_contest'))

    except Exception as e:
        flash(f'Произошла ошибка при создании соревнования: {str(e)}', 'error')
        return redirect(url_for('contest_list'))


@app.route("/contest/<contid>", methods=['GET'])
def contest(contid):
    if isLoggedin():
        return url_for('login')
    userid = session['id']
    if not DBoperations.isContestExpired(contid):
        try:
            # Достаем таски
            opponent_id = DBoperations.getEnemy(contid, userid)
            tasks_ids = DBoperations.takeTasksById(contid)
            if not tasks_ids:
                flash("Ошибка при загрузке заданий!")
                print(tasks_ids)
                abort(500)
            tasklist = list(map(int, tasks_ids[0].split(',')))
            tasks = {}
            for task in DBoperations.getTasksForContest(tasklist):
                tasks.update({task[0]: task})

            # Достаем айдишники
            player_solved = DBoperations.hasTaskSolvedByInContest(userid, contid)
            opponent_solved = DBoperations.hasTaskSolvedByInContest(opponent_id, contid)
            return render_template('contest.html', contid=contid, tasks=tasks, tasklist=tasklist,
                                   player_solved=player_solved,
                                   opponent_solved=opponent_solved)
        except ValueError:
            flash('Вы не можете смотреть соревнование, пока нет второго игрока!')
            return redirect(url_for('account'))
    else:
        flash("Это соревнование окончено!")
        return redirect(url_for('account'))


# Решение таски в соревновании
@app.route("/contest/<contid>/task/<taskid>", methods=['GET', 'POST'])
def solveContestTask(contid, taskid):
    if isLoggedin():
        return redirect(url_for('login'))
    if not DBoperations.isContestExpired(contid):
        msg = ""
        DBoperations.startSolving(session['id'], taskid, contid)
        solvationStatus = ""
        trigger = DBoperations.isSolved(session['id'], taskid,
                                        contid)
        taskInfo = DBoperations.getTask(taskid)
        print(taskInfo)
        task_name = taskInfo[4]
        complexity = taskInfo[2]
        theme = taskInfo[3]
        text = json.loads(taskInfo[9])
        description = text['desc']
        right_answer = DBoperations.getSolvation(taskid)

        try:
            res = DBoperations.howSolved(session['id'], taskid, contid)
            if res is None:
                solvationStatus = "Задача еще не решена"
            else:
                if res:
                    solvationStatus = f"<div class='solvedRight'>Задание решено верно</div>"
                else:
                    solvationStatus = f"<div class='solvedBad'>Задание решено неверно</div>"
        except Exception as e:
            print(e)
            pass
        if request.method == "GET":
            return render_template('solve_contest_task.html',
                                   taskid=taskid,
                                   task_name=task_name,
                                   complexity=complexity,
                                   theme=theme,
                                   description=description,
                                   trigger=trigger,
                                   solvationStatus=solvationStatus,
                                   contid=contid
                                   )

        if request.method == "POST":
            sent_answer = request.form.get('answer')
            emit('message', {'action': 'task_solvation', 'contest_id': contid}, broadcast=True, namespace="/")
            if sent_answer == "" or sent_answer == " ":
                msg = "Поле ответа не может быть пустым!"
            else:
                DBoperations.setSolvationTime(taskid, session['id'], contid)
                emit('message', 'task_solved', broadcast=True, namespace="/")
                if right_answer == sent_answer:
                    msg = "Задание решено верно!"
                    DBoperations.setSolvation(taskid, session['id'], True, contid)
                else:
                    DBoperations.setSolvation(taskid, session['id'], False, contid)
                    msg = f"Задание решено неверно!"

            return render_template('solve_contest_task.html',
                                   taskid=taskid,
                                   task_name=task_name,
                                   complexity=complexity,
                                   theme=theme,
                                   description=description,
                                   msg=msg,
                                   sent_answer=sent_answer,
                                   trigger=trigger,
                                   solvationStatus=solvationStatus,
                                   contid=contid
                                   )
        else:
            flash("Это соревнование еще не началось или уже окончено!")
            return redirect(url_for('account'))


@app.route('/admin-panel')
def admin_panel():
    if isLoggedin():
        return redirect(url_for('login'))
    if isAdministrator:
        return redirect(url_for('login'))
    return render_template('admin_panel.html')


if __name__ == '__main__':
    # app.run(debug=True, host="0.0.0.0", port=5000)
    socketio.run(app, debug=True, host="0.0.0.0", port=5000, allow_unsafe_werkzeug=True)
