import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
pg_password = os.getenv('PG_PASSWORD')

try:
    conn = psycopg2.connect(host="localhost", user="postgres", password=pg_password, port=5432, dbname="players")
    cursor = conn.cursor()
    
    print("Checking 'contests' table structure...")
    cursor.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'contests';")
    columns = cursor.fetchall()
    for col in columns:
        if col[0] in ['u1_result', 'u2_result']:
            print(f"Column: {col[0]}, Type: {col[1]}")

    print("\nChecking sample data from 'contests'...")
    cursor.execute("SELECT id, u1_result, u2_result FROM contests LIMIT 5;")
    rows = cursor.fetchall()
    for row in rows:
        print(f"ID: {row[0]}")
        print(f"  u1_result: {row[1]} (type: {type(row[1])})")
        print(f"  u2_result: {row[2]} (type: {type(row[2])})")

except Exception as e:
    print(f"Error: {e}")
finally:
    if 'conn' in locals() and conn:
        conn.close()
