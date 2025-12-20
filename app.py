from flask import Flask, blueprints, request, render_template, session
from hashlib import sha256
import re
import DBoperations
app = Flask(__name__)


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
            msg = "Успешный вход!"
        if account == None:
            msg = "Аккаунта не существует или введен некорректный пароль!"
    return render_template('login.html', msg=msg)


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

if __name__ == '__main__':
    app.run(debug=True)