import psycopg2
import json
from psycopg2.extras import DictCursor
from datetime import datetime
import bcrypt
conn = psycopg2.connect(host="localhost", user="postgres", password="TK", port=5432, dbname="players")
if conn:
    print("Connected")

cursor = conn.cursor()
#cursor.execute("SELECT id FROM tasks WHERE subject LIKE %s AND theme LIKE %s")
#И по умолчанию заменять на звездочку

def init_db():

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS registered_players 
(
player_id SERIAL NOT NULL,
player_name VARCHAR(32),
player_score INT DEFAULT 1000,
player_password VARCHAR(255) NOT NULL,
email VARCHAR(255) NOT NULL,
is_admin BOOLEAN DEFAULT FALSE,
PRIMARY KEY(player_id)
);
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS score_archive
(
    id SERIAL PRIMARY KEY,
    player_id INT NOT NULL,
    date DATE NOT NULL,
    player_score INT NOT NULL,
    UNIQUE(player_id, date)
);
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks(
    id SERIAL PRIMARY KEY,
    subject TEXT,
    complexity TEXT,
    theme TEXT,
    name TEXT,
    created DATE NOT NULL DEFAULT CURRENT_DATE,
    user_created INT,
    updated DATE NOT NULL DEFAULT CURRENT_DATE,
    user_updated INT,
    task TEXT,
    CONSTRAINT fk_user_created
        FOREIGN KEY (user_created) 
        REFERENCES registered_players (player_id),
    CONSTRAINT fk_user_updated
        FOREIGN KEY (user_updated) 
        REFERENCES registered_players (player_id)
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS solved_tasks(
    user_id INT NOT NULL,
    task_id INT NOT NULL,
    solved_at DATE NOT NULL DEFAULT CURRENT_DATE,
    is_right BOOLEAN,
    CONSTRAINT fk_user_solved
        FOREIGN KEY (user_id) 
        REFERENCES registered_players (player_id),
    CONSTRAINT fk_task_solved
        FOREIGN KEY (task_id) 
        REFERENCES tasks (id)
    )
    """)
    conn.commit()
    cursor.execute("SELECT * FROM registered_players")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO registered_players(player_name, player_password, email, is_admin) VALUES('admin', '$2b$12$wXK7021vkTPZBD10hDe8S.zn07MLXXLnqOgSElkTtSGgzr.Ac9lGm', 'admin@example.com', true)")
        cursor.execute("INSERT INTO registered_players(player_name, player_password, email, is_admin) VALUES('player', '$2b$12$wXK7021vkTPZBD10hDe8S.zn07MLXXLnqOgSElkTtSGgzr.Ac9lGm', 'admin@example.com', false)")
        conn.commit()
    cursor.execute("SELECT * FROM tasks")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO tasks(subject, complexity, theme, name, user_created, user_updated, task) VALUES ('Математика', 'Легкая', 'Квадратные уравнения', '47F947', 1, 1, '{\"desc\":\"В треугольнике ABC...\", \"hint\":\"Впишите ответ\", \"answer\":\"14,5\"}')")
        cursor.execute("INSERT INTO tasks(subject, complexity, theme, name, user_created, user_updated, task) VALUES ('Физика', 'Сложная', 'Термодинамика', '67A967', 1, 1, '{\"desc\":\"В треугольнике ABC...\", \"hint\":\"Впишите ответ\", \"answer\":\"14,5\"}')")
        conn.commit()



def checkUserEmail(email):
    cursor.execute("SELECT * FROM registered_players WHERE email = %s", (email,))
    return cursor.fetchone()


def checkUserName(username):
    cursor.execute("SELECT * FROM registered_players WHERE player_name = %s", (username,))
    return cursor.fetchone()


def addNewUser(username, email, password_hash):
    cursor.execute(
        "INSERT INTO registered_players(player_score, player_name, player_password, email) VALUES (1000, %s, %s, %s)", \
        (username, password_hash.decode('utf-8'), email))
    print(password_hash)
    conn.commit()


def loginUser(username, password):
    #cursor.execute("SELECT * FROM registered_players WHERE player_name = %s AND player_password = %s", \
     #              (username, password_hash))
    print(username)
    cursor.execute("SELECT * FROM registered_players WHERE player_name = %s", (username,))
    user = cursor.fetchone()
    if user:
        print(user)
        print( user[3].encode('utf-8'))
        if bcrypt.checkpw(password.encode(), user[3].encode('utf-8')):
            return user
    return None


def daily_score_backup():
    cursor.execute("SELECT * FROM registered_players")
    for i in cursor.fetchall():
        current_date = datetime.now().date()
        cursor.execute("INSERT INTO score_archive(player_id, date, player_score) VALUES(%s, %s, %s)",
                       (i[0], current_date, i[2]))
    conn.commit()


def takeScorebyDays(player_id: int):
    current_date = datetime.now().date()
    cursor.execute("SELECT date, player_score FROM score_archive WHERE player_id = %s AND date + 30 >= %s", \
                   (player_id, current_date))
    return cursor.fetchall()

def isAdmin(player_id: int):
    cursor.execute("SELECT * FROM registered_players WHERE player_id = %s AND is_admin = true", (player_id, ))
    return cursor.fetchone()

def addAdmin(player_id):
    cursor.execute("INSERT INTO admins(user_id) VALUES (%s)", (player_id, ))
    conn.commit()

def getTasks():
    cursor.execute("SELECT * FROM tasks ORDER BY id")
    return cursor.fetchall()

def addNewTask(task_name, subject, complexity, theme, description, answer):
    task = {"desc": description, "hint": "Введите правильный ответ", "answer": answer}
    task_json = json.dumps(task)
    cursor.execute("INSERT INTO tasks(subject, complexity, theme, name, user_created, user_updated, task) VALUES (%s, %s, %s, %s, %s, %s, %s)", \
                   (subject, complexity, theme, task_name, 1, 1, task_json))
    """
        CREATE TABLE IF NOT EXISTS tasks(
        id SERIAL PRIMARY KEY,
        subject TEXT,
        complexity TEXT,
        theme TEXT,
        name TEXT,
        created DATE NOT NULL DEFAULT CURRENT_DATE,
        user_created INT,
        updated DATE NOT NULL DEFAULT CURRENT_DATE,
        user_updated INT,
        task TEXT,
        CONSTRAINT fk_user_created
            FOREIGN KEY (user_created) 
            REFERENCES registered_players (player_id),
        CONSTRAINT fk_user_updated
            FOREIGN KEY (user_updated) 
            REFERENCES registered_players (player_id)
        );
        """
    conn.commit()

def getTask(taskid):
    cursor.execute("SELECT * FROM tasks WHERE id = %s", (taskid,))
    return cursor.fetchone()

def updateTask(id, task_name, subject, complexity, theme, description, answer):
    task = {"desc": description, "hint": "Введите правильный ответ", "answer": answer}
    task_json = json.dumps(task)
    cursor.execute("UPDATE tasks SET name = %s, subject = %s, complexity = %s, theme = %s, task=%s WHERE id = %s", \
                   (task_name, subject, complexity, theme, task_json, id, ))
    conn.commit()

def deleteTask(id):
    cursor.execute("DELETE FROM tasks WHERE id = %s", (id,))
    conn.commit()

def getSolvation(taskid):
    cursor.execute("SELECT task FROM tasks WHERE id = %s", (taskid,))
    task_json = "".join(cursor.fetchone())
    task = json.loads(task_json)
    return task['answer']
def setSolvation(taskid, userid, isright):
    cursor.execute("INSERT INTO solved_tasks(user_id, task_id, is_right) VALUES (%s, %s, %s)", \
                   (userid, taskid, isright))
    conn.commit()
    """CREATE TABLE IF NOT EXISTS solved_tasks(
    user_id INT NOT NULL,
    task_id INT NOT NULL,
    solved_at DATE NOT NULL DEFAULT CURRENT_DATE,
    is_right BOOLEAN,
    CONSTRAINT fk_user_solved
        FOREIGN KEY (user_id) 
        REFERENCES registered_players (player_id),
    CONSTRAINT fk_task_solved
        FOREIGN KEY (task_id) 
        REFERENCES tasks (id)
    )
    """
def solvedTasksBy(userid, taskid):
    cursor.execute("SELECT * FROM solved_tasks WHERE user_id = %s AND task_id = %s", (userid, taskid,))
    if cursor.fetchone():
        return True
    return False
def howSolved(userid, taskid):
    cursor.execute("SELECT is_right FROM solved_tasks WHERE user_id = %s AND task_id = %s", (userid, taskid,))
    return cursor.fetchone()[0]

def isSolved(userid, taskid):
    cursor.execute("SELECT * FROM solved_tasks WHERE user_id = %s AND task_id = %s", (userid, taskid,))
    if cursor.fetchone():
        return True
    return False

def taskFilter(subject, theme, complexity):
    filter = []
    values = []
    if subject != "":
        filter.append("subject = %s")
        values.append(subject)
    if theme != "":
        filter.append("theme = %s")
        values.append(theme)
    if complexity != "":
        filter.append("complexity = %s")
        values.append(complexity)
    if len(filter) == 0:
        filter_str = ""
    else:
        filter_str = "WHERE " + " AND ".join(filter)
    cursor.execute(f"SELECT id FROM tasks {filter_str}", tuple(values))
    ids = [int("".join(map(str, i))) for i in cursor.fetchall()]
    return ids

def listSubjects():
    cursor.execute("SELECT DISTINCT subject FROM tasks")
    subjects = [""] + ["".join(map(str, i)) for i in cursor.fetchall()]
    return subjects
print(listSubjects())