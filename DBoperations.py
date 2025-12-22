import psycopg2
from psycopg2.extras import DictCursor
from datetime import datetime
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
    conn.commit()
init_db()
def checkUserEmail(email):
    cursor.execute("SELECT * FROM registered_players WHERE email = %s", (email,))
    return cursor.fetchone()

def checkUserName(username):
    cursor.execute("SELECT * FROM registered_players WHERE player_name = %s", (username,))
    return cursor.fetchone()

def addNewUser(username, email, password_hash):
    cursor.execute("INSERT INTO registered_players(player_score, player_name, player_password, email) VALUES (1000, %s, %s, %s)",\
                   (username, password_hash, email))
    conn.commit()

def loginUser(username, password_hash):
    cursor.execute("SELECT * FROM registered_players WHERE player_name = %s AND player_password = %s", \
                   (username, password_hash))
    return cursor.fetchone()

def daily_score_backup():
    cursor.execute("SELECT * FROM registered_players")
    for i in cursor.fetchall():
        current_date = datetime.now().date()
        cursor.execute("INSERT INTO score_archive(player_id, date, player_score) VALUES(%s, %s, %s)", (i[0],current_date, i[2]))
    conn.commit()
daily_score_backup()
cursor.execute("SELECT * FROM score_archive")
print(cursor.fetchall())