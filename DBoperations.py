import psycopg2
from psycopg2.extras import DictCursor
from datetime import datetime
import bcrypt
conn = psycopg2.connect(host="localhost", user="postgres", password="TK", port=5432, dbname="players")
if conn:
    print("Connected")

cursor = conn.cursor()


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
    year DATE,
    olympiad TEXT,
    difficulty INT,
    grade INT,
    answer TEXT,
    stage INT,
    subject TEXT,
    UNIQUE(id)
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS solvedTasks(
    id SERIAL PRIMARY KEY,
    task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL,
    solved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(task_id, user_id)
    );
    """)
    conn.commit()
    cursor.execute("SELECT * FROM registered_players")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO registered_players(player_name, player_password, email, is_admin) VALUES('admin', '$2b$12$wXK7021vkTPZBD10hDe8S.zn07MLXXLnqOgSElkTtSGgzr.Ac9lGm', 'admin@example.com', true)")
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