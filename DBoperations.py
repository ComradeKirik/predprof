import psycopg2
from psycopg2.extras import DictCursor
conn = psycopg2.connect(host="localhost", user="postgres", password="TK", port=5432, dbname="players")
if conn:
    print("Connected")



cursor = conn.cursor()

def checkUserEmail(email):
    cursor.execute("SELECT * FROM registered_players WHERE email = %s", (email,))
    return cursor.fetchone()

def checkUserName(username):
    cursor.execute("SELECT * FROM registered_players WHERE player_name = %s", (username,))
    return cursor.fetchone()

def addNewUser(username, email, password):
    cursor.execute("INSERT INTO registered_players(player_score, player_name, player_password, email) VALUES (1000, %s, %s, %s,)",\
                   (username, password, email))
    conn.commit()
