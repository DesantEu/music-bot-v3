from mysql.connector.aio import connect
from mysql.connector.aio.abstracts import MySQLConnectionAbstract, MySQLCursorAbstract
import os, time, json

cnx: MySQLConnectionAbstract
cursor: MySQLCursorAbstract

async def init():
    global cnx, cursor
    cnx = await connect(
        host="mysql",
        user="root",
        password=os.environ["MYSQL_ROOT_PASSWORD"],
        connection_timeout=10000,
        database="discord"
    )
    print(cnx)


async def create_cache():
    cursor = await cnx.cursor()

    query = (
        "CREATE TABLE cache ("
        "id        INT AUTO_INCREMENT PRIMARY KEY,"
        "video_id  VARCHAR(255),"
        "title     VARCHAR(255),"
        "duration  VARCHAR(100),"
        "searches  JSON"
        ");"
        )
    await cursor.execute(query)

    res = await cursor.fetchall()
    print(f"{cursor.statement}: {res}")


    await cursor.close()
    


async def add_cache(video_id: str, title:str, duration: str, searches: list[str]):
    cursor = await cnx.cursor()
    # searches_json = (i for i in searches)
    # print(searches_json)

    query = (
        "INSERT INTO cache(video_id, title, duration, searches)"
        f"VALUES (%s, %s, %s, '{str(searches).replace("'", '"')}');" 
        )
    data = (video_id, title, duration)

    await cursor.execute(query, data)
    await cnx.commit()

    res = await cursor.fetchall()
    print(f"{cursor.statement}: {res}")


    await cursor.close()


async def select_cache():
    cursor = await cnx.cursor()
    query = (
        "SELECT * FROM cache;"
    )
    await cursor.execute(query)

    res = await cursor.fetchall()
    print(f"{cursor.statement}: {res}")

    await cursor.close()



async def drop_cache():
    cursor = await cnx.cursor()

    query = (
        "DROP TABLE cache;"
    )
    await cursor.execute(query)

    res = await cursor.fetchall()
    print(f"{cursor.statement}: {res}")


    await cursor.close()
