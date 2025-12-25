from flask import Flask, blueprints, request, render_template, session, url_for, redirect
from hashlib import sha256
import re
import DBoperations
from dotenv import load_dotenv
import os
import json
app = Flask(__name__)
load_dotenv()
app.secret_key = os.getenv('SECRET_KEY')
DBoperations.init_db()
@app.route("/")
def mainpage():
    return render_template('main.html')

@app.route("/login", methods=["GET", "POST"])
def login():
    msg = ""
    if request.method == "POST" and "username" in request.form and "password" in request.form:
        username = request.form.get("username")
        password = request.form.get("password")
        password_hash = sha256(password.encode('utf-8')).hexdigest()
        account = DBoperations.loginUser(username, password_hash)
        if account:
            session['loggedin'] = True
            session['id'] = account[0]
            session['username'] = account[1]
            session['email'] = account[4]
            profile_pic_path = f"static/profile_pics/pic_{session['id']}.jpg"
            if os.path.exists(profile_pic_path):
                session['profile_pic'] = f"/static/profile_pics/pic_{session['id']}.jpg"
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
        password_hash = sha256(password.encode('utf-8')).hexdigest()

        if DBoperations.checkUserEmail(email) != None:
            msg = "Данная почта уже зарегистрирована"
        elif not re.match(r"^[A-Za-z0-9_]+$", username):
            msg = "Запрещенные символы в имени. Разрешена латиница, цифры и _"
        elif DBoperations.checkUserName(username) != None:
            msg = "Данный никнейм уже используется!"
        elif not username or not email or not password:
            msg = "Пожалуйста, заполните все поля!"
        else:
            DBoperations.addNewUser(username, email, password_hash)
            return redirect(url_for('dashboard'))

    return render_template('register.html', msg=msg)


@app.route("/dashboard")
def dashboard():
    try:
        # Таблички
        scores = DBoperations.takeScoreByDays(session['id'])
        chart_data = []
        for date, score in scores:
            chart_data.append([date.strftime("%Y-%m-%d"), score])

        # Преобразуем в JSON строку
        chart_data = json.dumps(chart_data)
        #Фото профиля
        profile_pic_path = f"static/profile_pics/pic_{session['id']}.jpg"
        if not os.path.exists(profile_pic_path):
            print("not exists")
            profile_pic = "static/profile_pics/generic_profile_picture.jpg"
        else:
            profile_pic = f"static/profile_pics/pic_{session['id']}.jpg"
        print(profile_pic)
        return render_template('dashboard.html',
                               chart_data_json=chart_data,
                               profile_pic=profile_pic,
                               username=session.get('username', 'Пользователь'))
    except KeyError:
        return redirect(url_for('login'))

@app.context_processor
def inject_user_data():
    if 'loggedin' in session and session['loggedin']:
        return dict(
            loggedin=True,
            username=session.get('username'),
            profile_pic=session.get('profile_pic', '/static/profile_pics/generic_profile_picture.jpg'),
            user_id=session.get('id')
        )
    return dict(
        loggedin=False,
        profile_pic="/static/profile_pics/generic_profile_picture.jpg",
        username=None
    )

if __name__ == '__main__':
    app.run(debug=True)