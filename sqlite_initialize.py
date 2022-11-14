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
		
def init_osu_verification(cursor):
    queries = []

    queries.append("DROP TABLE IF EXISTS OsuVerification;")
    queries.append("CREATE TABLE IF NOT EXISTS OsuVerification (discord_id INT primary key, osu_id INT, osu_name STRING, verification_code STRING, time DATETIME);")

    for query in queries:
        execute_and_log(cursor, query)
        
def init_osu_song_quiz(cursor):
    queries = []
    queries.append("DROP TABLE IF EXISTS OsuQuiz;")
    queries.append("CREATE TABLE IF NOT EXISTS OsuQuiz (server_id INT, mapset_id INT, song_name STRING);")
    queries.append("DROP TABLE IF EXISTS OsuQuizSettings;")
    queries.append("CREATE TABLE IF NOT EXISTS OsuQuizSettings (server_id INT, length INT DEFAULT 1000, timeout INT DEFAULT 60);")
    
    for query in queries:
        execute_and_log(cursor, query)

try:
    sqliteConnection = sqlite3.connect(DBPATH)
    cursor = sqliteConnection.cursor()
    print("Database is created and Successfully Connected to SQLite")
    
    options = ["last_update", "osu_id_connection", "osu_verification", "osu_song_quiz"]
    func = [init_last_update, init_osu_id_connection, init_osu_verification, init_osu_song_quiz]
    
    choice = None
    print("Choose database you want to reset, -1 to reset everything.")
    print("==")
    for i, option in enumerate(options):
        print(i, ": ", option)
    print("==")

    #while choice is None:
    #    try:
    #        choice = int(input())
    #    except:
    #        continue
    
    for choice in range(len(func)):
        if 0 <= choice < len(func):
            func[choice](cursor)
        else:
            for i in range(len(func)):
                func[i](cursor)

    cursor.close()

except sqlite3.Error as error:
    print("Error while connecting to sqlite", error)
    sys.exit(0)

finally:
    if (sqliteConnection):
        sqliteConnection.commit()
        sqliteConnection.close()
        print("The SQLite connection is closed")