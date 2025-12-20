from flask import Flask, blueprints, request, render_template
app = Flask(__name__)

@app.route("/")
def mainpage():
    return render_template('main.html')

@app.route("/register")
def register():
    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)