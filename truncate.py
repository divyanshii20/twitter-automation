import pymysql

def get_db_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="Divyanshi@1",
        database="twitter",
        cursorclass=pymysql.cursors.DictCursor
    )

conn = get_db_connection()
cursor = conn.cursor()
cursor.execute("truncate table scrapped_tweets")

conn.commit()
conn.close()
