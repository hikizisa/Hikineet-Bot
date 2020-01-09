import sys, os
import sqlite3
from datetime import date, datetime, time, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()
DBPATH = os.getenv('DB_PATH')

def execute_and_log(cursor, query):
    cursor.execute(query)
    print("Query: ", query, "\n")
    record = cursor.fetchall()
    print("Result: ", record, "\n")

def init_last_update(cursor):
    tz = timezone(timedelta(hours=0))
    time = datetime.now(tz = tz) - timedelta(hours=24)
    sql_time = time.strftime('%Y-%m-%d %H:%M:%S')

    queries = []
    
    queries.append("DROP TABLE IF EXISTS LastUpdate;")
    queries.append("CREATE TABLE LastUpdate (time DATETIME);")
    queries.append("INSERT INTO LastUpdate VALUES('" + sql_time + "');")
    queries.append("SELECT * FROM LastUpdate;")

    for query in queries:
        execute_and_log(cursor, query)

def init_osu_id_connection(cursor):
    queries = []

    queries.append("CREATE TABLE IF NOT EXISTS OsuUserName (discord_id INT primary key, osu_id INT, osu_name STRING);")

    for query in queries:
        execute_and_log(cursor, query)

try:
    sqliteConnection = sqlite3.connect(DBPATH)
    cursor = sqliteConnection.cursor()
    print("Database created and Successfully Connected to SQLite")
	
    init_last_update(cursor)
    init_osu_id_connection(cursor)

    cursor.close()

except sqlite3.Error as error:
    print("Error while connecting to sqlite", error)
    sys.exit(0)

finally:
    if (sqliteConnection):
        sqliteConnection.commit()
        sqliteConnection.close()
        print("The SQLite connection is closed")