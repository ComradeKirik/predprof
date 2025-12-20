from flask import Flask, blueprints, request, render_template
from hashlib import sha256
import re
import DBoperations
app = Flask(__name__)


@app.route("/")
def mainpage():
    return render_template('main.html')

@app.route("/register", methods="POST")
def register():
    msg = ""
    if request.method == "POST" and "username" in request.form and "password" in request.form and "email" in request.form:
        username = request.form.get("username")
        password = sha256(request.form.get("password"))
        email = request.form.get("email")
        if DBoperations.checkUserEmail(email) != None:
            msg = "Данная почта уже зарегистрирована"
        elif not re.match(r"[A-Za-z0-9_]", username):
            msg = "Запрещенные символы в имени. Разрешена латиница, цифры и _"
        elif DBoperations.checkUserName(username) != None:
            msg = "Данный никнейм уже используется!"
        elif not username or not email or not password:
            msg = "Пожалуйста, заполните все поля!"
        else:
            DBoperations.addNewUser(username, email, password)
            msg = "Успешная регистрация!"

    return render_template('register.html', msg=msg)

if __name__ == '__main__':
    app.run(debug=True)