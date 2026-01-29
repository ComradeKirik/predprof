import psycopg2
import json
from psycopg2.extras import DictCursor
from datetime import datetime
import bcrypt

conn = psycopg2.connect(host="localhost", user="postgres", password="TK", port=5432, dbname="players")
if conn:
    print("Connected")

cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

# cursor.execute("SELECT id FROM tasks WHERE subject LIKE %s AND theme LIKE %s")
# И по умолчанию заменять на звездочку
"""  Таблица для хранения соревнований в базе данных (Предмет, Уровень сложности, Количество заданий, Возможность повторного ответа при ошибке, Время начала, Продолжительность, 
Участник1 (создатель), Участник2 (принявший вызов), Результат пользователя 1, Результат пользователя 2, Победитель, Статус поединка, Подпись участника1,Подпись участника2)"""


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
    contest_id INT DEFAULT NULL,
    CONSTRAINT fk_user_solved
        FOREIGN KEY (user_id) 
        REFERENCES registered_players (player_id),
    CONSTRAINT fk_task_solved
        FOREIGN KEY (task_id) 
        REFERENCES tasks (id)
    )
    """)
    # u1 - тот, кто вызвал на поединок(или создал его, не является админом)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contests(
        id SERIAL PRIMARY KEY,
        subject TEXT NOT NULL,
        complexity TEXT NOT NULL,
        started_at TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP,
        ending_at TIMESTAMP(0) DEFAULT NULL,
        user_1 INT NOT NULL,
        user_2 INT DEFAULT NULL,
        u1_result TEXT,
        u2_result TEXT,
        winner INT,
        status TEXT,
        u1_accepted BOOLEAN DEFAULT NULL,
        u2_accepted BOOLEAN DEFAULT NULL,
        CONSTRAINT fk_p1
            FOREIGN KEY (user_1) 
            REFERENCES registered_players (player_id),
        CONSTRAINT fk_p2
            FOREIGN KEY (user_2) 
            REFERENCES registered_players (player_id)
        
        )
        """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS task_in_process(
        user_id INT NOT NULL,
        task_id INT NOT NULL,
        is_hinted BOOLEAN DEFAULT FALSE,
        started_at TIMESTAMP  DEFAULT CURRENT_TIMESTAMP,
        ended_at TIMESTAMP  DEFAULT NULL,
        contest_id INT DEFAULT NULL,
        PRIMARY KEY (user_id, task_id),
        CONSTRAINT fk_user_solved
            FOREIGN KEY (user_id) 
            REFERENCES registered_players (player_id),
        CONSTRAINT fk_task_solved
            FOREIGN KEY (task_id) 
            REFERENCES tasks (id),
        CONSTRAINT fk_contest_id
            FOREIGN KEY (contest_id) 
            REFERENCES contests (id)
        )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS contest_tasks(
        contest_id INT NOT NULL,
        tasks_ids TEXT NOT NULL,
        CONSTRAINT fk_contest_id
            FOREIGN KEY (contest_id)
            REFERENCES contests (id)
    )
    """)
    conn.commit()
    cursor.execute("SELECT * FROM registered_players")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO registered_players(player_name, player_password, email, is_admin) VALUES('admin', '$2b$12$wXK7021vkTPZBD10hDe8S.zn07MLXXLnqOgSElkTtSGgzr.Ac9lGm', 'admin@example.com', true)")
        cursor.execute(
            "INSERT INTO registered_players(player_name, player_password, email, is_admin) VALUES('player', '$2b$12$wXK7021vkTPZBD10hDe8S.zn07MLXXLnqOgSElkTtSGgzr.Ac9lGm', 'admin@example.com', false)")
        cursor.execute(
            "INSERT INTO registered_players(player_name, player_password, email, is_admin) VALUES('player2', '$2b$12$wXK7021vkTPZBD10hDe8S.zn07MLXXLnqOgSElkTtSGgzr.Ac9lGm', 'admin@example.com', false)")
        conn.commit()
    cursor.execute("SELECT * FROM tasks")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO tasks(subject, complexity, theme, name, user_created, user_updated, task) VALUES ('Математика', 'Легкая', 'Квадратные уравнения', '47F947', 1, 1, '{\"desc\":\"В треугольнике ABC...\", \"hint\":\"Впишите ответ\", \"answer\":\"14,5\"}')")
        cursor.execute(
            "INSERT INTO tasks(subject, complexity, theme, name, user_created, user_updated, task) VALUES ('Математика', 'Легкая', 'Квадратные неравенства', '4AD198', 1, 1, '{\"desc\":\"В треугольнике ABC...\", \"hint\":\"Впишите ответ\", \"answer\":\"14,5\"}')")

        cursor.execute(
            "INSERT INTO tasks(subject, complexity, theme, name, user_created, user_updated, task) VALUES ('Физика', 'Сложная', 'Термодинамика', '67A967', 1, 1, '{\"desc\":\"В треугольнике ABC...\", \"hint\":\"Впишите ответ\", \"answer\":\"14,5\"}')")
        conn.commit()
    cursor.execute("SELECT * FROM contests")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO contests(subject, complexity, can_reanswer, started_at, ending_at, user_1, user_2, u1_result, u2_result, winner, status, u1_accepted, u2_accepted) VALUES ('Математика', 'Легкая', now() - interval '3 hours', now(), 2, 3, 10, 12, 3, 'Окончено', true, true)")
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
    conn.commit()


def loginUser(username, password):
    # cursor.execute("SELECT * FROM registered_players WHERE player_name = %s AND player_password = %s", \
    #              (username, password_hash))
    print(username)
    cursor.execute("SELECT * FROM registered_players WHERE player_name = %s", (username,))
    user = cursor.fetchone()
    print(user)
    if user:
        if bcrypt.checkpw(password.encode(), user['player_password'].encode('utf-8')):
            return user
    return None


def daily_score_backup():
    cursor.execute("SELECT * FROM registered_players")
    for i in cursor.fetchall():
        current_date = datetime.now().date()
        cursor.execute("INSERT INTO score_archive(player_id, date, player_score) VALUES(%s, %s, %s)",
                       (i[0], current_date, i[2]))
    conn.commit()


def deleteAccount(userid):
    try:
        # 1. Сначала удаляем контесты, где пользователь является создателем (user_1)
        cursor.execute("DELETE FROM contests WHERE user_1 = %s", (userid,))

        # 2. Обновляем контесты, где пользователь является user_2 (ставим user_2 в NULL)
        cursor.execute("""
            UPDATE contests 
            SET user_2 = NULL, 
                u2_result = NULL,
                u2_accepted = NULL,
                status = CASE 
                    WHEN status = 'active' AND user_1 IS NOT NULL THEN 'waiting' 
                    ELSE status 
                END
            WHERE user_2 = %s
        """, (userid,))

        # 3. Обновляем задачи, где пользователь был создателем или обновителем
        cursor.execute("""
            UPDATE tasks 
            SET user_created = NULL, 
                user_updated = NULL 
            WHERE user_created = %s OR user_updated = %s
        """, (userid, userid))

        # 4. Удаляем записи о решенных задачах пользователя
        cursor.execute("DELETE FROM solved_tasks WHERE user_id = %s", (userid,))

        # 5. Удаляем задачи в процессе решения
        cursor.execute("DELETE FROM task_in_process WHERE user_id = %s", (userid,))

        # 6. Удаляем историю очков
        cursor.execute("DELETE FROM score_archive WHERE player_id = %s", (userid,))

        # 7. Обновляем контесты, где пользователь является победителем
        cursor.execute("""
            UPDATE contests 
            SET winner = NULL 
            WHERE winner = %s
        """, (userid,))

        # 8. Наконец удаляем самого пользователя
        cursor.execute("DELETE FROM registered_players WHERE player_id = %s", (userid,))

        conn.commit()
        print(f"Аккаунт пользователя {userid} успешно удален")
        return True

    except Exception as e:
        conn.rollback()
        print(f"Ошибка при удалении аккаунта: {e}")
        return False


def takeScorebyDays(player_id: int):
    current_date = datetime.now().date()
    cursor.execute("SELECT date, player_score FROM score_archive WHERE player_id = %s AND date + 30 >= %s", \
                   (player_id, current_date))
    return cursor.fetchall()


def isAdmin(player_id: int):
    cursor.execute("SELECT * FROM registered_players WHERE player_id = %s AND is_admin = true", (player_id,))
    return cursor.fetchone()


def addAdmin(player_id):
    cursor.execute("INSERT INTO admins(user_id) VALUES (%s)", (player_id,))
    conn.commit()


def getTasks():
    cursor.execute("SELECT * FROM tasks ORDER BY id")
    return cursor.fetchall()


def addNewTask(task_name, subject, complexity, theme, description, answer, hint, userid):
    task = {"desc": description, "hint": hint, "answer": answer}
    task_json = json.dumps(task)
    cursor.execute(
        "INSERT INTO tasks(subject, complexity, theme, name, user_created, user_updated, task) VALUES (%s, %s, %s, %s, %s, %s, %s)", \
        (subject, complexity, theme, task_name, userid, userid, task_json))
    conn.commit()


def getTask(taskid):
    cursor.execute("SELECT * FROM tasks WHERE id = %s", (taskid,))
    return cursor.fetchone()


def updateTask(id, task_name, subject, complexity, theme, description, answer, hint):
    task = {"desc": description, "hint": hint, "answer": answer}
    task_json = json.dumps(task)
    cursor.execute("UPDATE tasks SET name = %s, subject = %s, complexity = %s, theme = %s, task=%s WHERE id = %s", \
                   (task_name, subject, complexity, theme, task_json, id,))
    conn.commit()


def deleteTask(id):
    cursor.execute("DELETE FROM tasks WHERE id = %s", (id,))
    conn.commit()


def getSolvation(taskid):
    cursor.execute("SELECT task FROM tasks WHERE id = %s", (taskid,))
    task_json = "".join(cursor.fetchone())
    task = json.loads(task_json)
    return task['answer']


def setSolvation(taskid, userid, isright, contid=None):
    cursor.execute("INSERT INTO solved_tasks(user_id, task_id, is_right, contest_id) VALUES (%s, %s, %s, %s)", \
                   (userid, taskid, isright, contid))
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


def howSolved(userid, taskid, contid=-1):
    """if contid is None:
        cursor.execute("SELECT is_right FROM solved_tasks WHERE user_id = %s AND task_id = %s AND contest_id IS NULL", (userid, taskid,))
    else:
        cursor.execute("SELECT is_right FROM solved_tasks WHERE user_id = %s AND task_id = %s AND contest_id = %s", (userid, taskid, contid,))"""
    cursor.execute(
        "SELECT is_right FROM solved_tasks WHERE user_id = %s AND task_id = %s AND coalesce(contest_id, -1) = %s",
        (userid, taskid, contid,))
    result = cursor.fetchone()
    if result is None:
        return None
    return result[0]


def isSolved(userid, taskid, contid=None):
    cursor.execute("SELECT * FROM solved_tasks WHERE user_id = %s AND task_id = %s AND contest_id = %s",
                   (userid, taskid, contid))
    if cursor.fetchone():
        return True
    return False


def startSolving(userid, taskid, contid=None):
    cursor.execute(
        "INSERT INTO task_in_process(user_id, task_id) VALUES(%s, %s) ON CONFLICT(user_id, task_id) DO NOTHING",
        (userid, taskid))
    conn.commit()


def setSolvationTime(taskid, userid, contid=None):
    cursor.execute("UPDATE task_in_process SET ended_at = CURRENT_TIMESTAMP WHERE task_id = %s AND user_id = %s ",
                   (taskid, userid))
    conn.commit()


def setHintStatus(taskid, userid):
    cursor.execute("UPDATE task_in_process SET is_hinted = true WHERE task_id = %s AND user_id = %s", (taskid, userid))
    conn.commit()


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


def exportToJSON(taskid):
    cursor.execute("SELECT subject, complexity, theme, name, task FROM tasks WHERE id=%s", (taskid,))
    task = dict(cursor.fetchone())
    JSON_task = json.dumps(task, default=str, ensure_ascii=False)
    # with open(f"static/json/file_{taskid}.json", "w+", encoding="utf-8") as file:
    #    file.write(JSON_task)
    #    return JSON_task
    return JSON_task


def importFromJSON(userid, taskJSON):
    task = json.loads(taskJSON)
    print(type(task), "it's type!")
    for i in task:
        print(i)
    inner_text = json.loads(task['task'])
    # Атата, здесь обнаружил ошибку с добавлением задания. Автором задания всегда указывается айди 1, т.е. если админом станет айди 3, то убдет плохо.
    addNewTask(task['name'], task['subject'], task['complexity'], task['theme'], inner_text['desc'],
               inner_text['answer'], inner_text['hint'], userid)


def listContests():
    query = """
        SELECT * FROM contests
    """
    cursor.execute(query)
    return cursor.fetchall()


def listUnexpiredContests():
    query = """
        SELECT * FROM contests WHERE status != 'Окончено'
    """
    cursor.execute(query)
    return cursor.fetchall()


def takeUserNameById(userid):
    cursor.execute("SELECT player_name FROM registered_players WHERE id = %s", (userid,))


def createNewContest(data: dict, user1=None):
    try:
        # Валидация обязательных полей
        required_fields = ['subject', 'complexity', 'started_at', 'ending_at']
        for field in required_fields:
            if not data.get(field):
                raise ValueError(f"Обязательное поле '{field}' не заполнено")

        # Валидация user1 (инициатора соревнования)
        if not user1:
            raise ValueError("ID первого пользователя должен быть целым числом")

        # Преобразование времени с обработкой ошибок
        today = datetime.now().date()

        try:
            started_time = datetime.strptime(data['started_at'], "%H:%M").time()
            ended_time = datetime.strptime(data['ending_at'], "%H:%M").time()
        except ValueError as e:
            raise ValueError(f"Некорректный формат времени: {e}")

        started_datetime = datetime.combine(today, started_time)
        ended_datetime = datetime.combine(today, ended_time)

        # Проверка логики времени (начало должно быть раньше конца)
        if started_datetime >= ended_datetime:
            raise ValueError("Время начала должно быть раньше времени окончания")

        u1_accepted = bool(data.get('u1_accepted', True))

        # Валидация user_2 (опционально)
        user_2 = data.get('user_2')
        if user_2 is not None:
            try:
                user_2 = int(user_2)
            except (ValueError, TypeError):
                raise ValueError("ID второго пользователя должен быть целым числом")

        # Работа с базой данных
        contest_data = {
            'subject': data['subject'].strip(),
            'complexity': data['complexity'],
            'started_at': started_datetime,
            'ending_at': ended_datetime,
            'user_1': user1,
            'user_2': user_2,
            'u1_accepted': u1_accepted
        }

        cursor.execute(
            """INSERT INTO contests 
            (subject, complexity, started_at, ending_at, 
             user_1, user_2, u1_accepted, status) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id""",
            (contest_data['subject'],
             contest_data['complexity'],
             contest_data['started_at'],
             contest_data['ending_at'],
             contest_data['user_1'],
             contest_data['user_2'],
             contest_data['u1_accepted'],
             'Ожидается')
        )

        contest_id = cursor.fetchone()[0]
        conn.commit()
        # Наполнение таблицы заданий
        cursor.execute(
            "SELECT id FROM tasks WHERE subject = %s AND complexity = %s ORDER BY random() LIMIT %s", \
            (contest_data['subject'], contest_data['complexity'], 5))
        tasks = cursor.fetchall()
        task_ids = ','.join(list(map(lambda x: str(x[0]), tasks)))
        cursor.execute("INSERT INTO contest_tasks VALUES(%s, %s)", (contest_id, task_ids))
        conn.commit()
        return contest_id

    except ValueError as e:
        print(f"Ошибка валидации данных: {e}")
        if conn:
            conn.rollback()
        raise

    except psycopg2.Error as e:
        print(f"Ошибка базы данных при создании соревнования: {e}")
        if conn:
            conn.rollback()
        raise

    except Exception as e:
        print(f"Неожиданная ошибка при создании соревнования: {e}")
        if conn:
            conn.rollback()
        raise


def isUserInContest(userid, contid):
    cursor.execute("SELECT user_1 FROM CONTESTS WHERE id=%s AND (user_1 = %s OR user_2 = %s)",
                   (contid, userid, userid,))
    return cursor.fetchone()


def addUserToContest(userid, contid):
    cursor.execute("UPDATE contests SET user_2 = %s, u2_accepted = true WHERE id = %s", (userid, contid,))
    conn.commit()


# Просмотреть все соревнования, в которых участвовал пользователь
def takeContestsByUid(userid):
    cursor.execute("SELECT * FROM contests WHERE user_1 = %s OR user_2 = %s", (userid, userid,))
    return cursor.fetchall()


def isUserInvited(userid):
    cursor.execute("SELECT user_2, u2_accepted FROM contests WHERE user_2 = %s", (userid,))
    return cursor.fetchall()


def takeTasksById(contid):
    cursor.execute("SELECT tasks_ids FROM contest_tasks WHERE contest_id = %s", (contid,))
    return cursor.fetchone()


def getTasksForContest(tasklist):
    cursor.execute("SELECT * FROM tasks WHERE id IN %(l)s", {'l': tuple(tasklist)})
    return cursor.fetchall()


# Получает айди противника в контесте
def getEnemy(contid, userid):
    cursor.execute("SELECT (user_1, user_2) FROM contests WHERE id = %s", (contid,))
    res = list(map(int, cursor.fetchone()[0].strip('()').split(',')))
    res.remove(userid)
    return res[0]


def hasTaskSolvedByInContest(userid, contid):
    cursor.execute("SELECT task_id, is_right FROM solved_tasks WHERE user_id = %s AND contest_id = %s",
                   (userid, contid))
    result = dict(cursor.fetchall())
    return result


def checkContestExpiration():
    now = datetime.now().replace(microsecond=0)
    query = """
                UPDATE contests 
                SET status = 'Окончено' 
                WHERE status != 'Окончено' 
                AND ending_at <= %s
            """
    cursor.execute(query, (now,))
    conn.commit()


def checkContestStart():
    now = datetime.now().replace(microsecond=0)
    query = """
        UPDATE contests 
        SET status = 'Идет' 
        WHERE status = 'Создано' AND started_at <= %s
    """
    cursor.execute(query, (now,))
    conn.commit()


def isContestExpired(contid):
    cursor.execute("SELECT status FROM contests WHERE id = %s", (contid,))
    if cursor.fetchone()[0] == "Окончено":
        return True
    return False
