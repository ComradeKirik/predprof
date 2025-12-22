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
            msg = "Успешный вход!"
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
            msg = "Успешная регистрация!"

    return render_template('register.html', msg=msg)


@app.route("/dashboard")
def dashboard():
    scores = DBoperations.takeScoreByDays(session['id'])
    chart_data = []
    for date, score in scores:
        chart_data.append([date.strftime("%Y-%m-%d"), score])

    # Преобразуем в JSON строку
    chart_data_json = json.dumps(chart_data)
    return render_template('dashboard.html',
                           chart_data_json=chart_data_json,
                           username=session.get('username', 'Пользователь'))

if __name__ == '__main__':
    app.run(debug=True)