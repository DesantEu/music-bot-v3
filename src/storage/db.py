from mysql.connector.aio import connect
from mysql.connector.aio.abstracts import MySQLConnectionAbstract, MySQLCursorAbstract
import os

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
    await create_tables()


async def create_tables():
    cursor = await cnx.cursor()

    # songs

    check = (
        "SHOW TABLES LIKE 'songs';"
    )

    await cursor.execute(check)
    res = await cursor.fetchall()

    if res == []:
        query = (
            "CREATE TABLE songs ("
            "id       VARCHAR(255) PRIMARY KEY,"
            "title    VARCHAR(255)"
            ");"
            )
        await cursor.execute(query)

        res = await cursor.fetchall()
        print(f"{cursor.statement}: {res}")
    else:
        print("table songs exists")


    # playlists

    check = (
        "SHOW TABLES LIKE 'playlists';"
    )

    await cursor.execute(check)
    res = await cursor.fetchall()

    if res == []:
        query = (
            "CREATE TABLE playlists ("
            "id    VARCHAR(255) PRIMARY KEY,"
            "title VARCHAR(255)"
            ");"
            )
        await cursor.execute(query)

        res = await cursor.fetchall()
        print(f"{cursor.statement}: {res}")
    else:
        print("table playlists exists")


    # searches

    check = (
        "SHOW TABLES LIKE 'searches';"
    )

    await cursor.execute(check)
    res = await cursor.fetchall()

    if res == []:
        query = (
            "CREATE TABLE searches ("
            "id    INT AUTO_INCREMENT PRIMARY KEY,"
            "query VARCHAR(255),"
            "v_id   VARCHAR(255),"
            "FOREIGN KEY (v_id) REFERENCES songs(id)"
            ");"
            )
        await cursor.execute(query)

        res = await cursor.fetchall()
        print(f"{cursor.statement}: {res}")
    else:
        print("table searches exists")


    # playlist songs many to many

    check = (
        "SHOW TABLES LIKE 'playlist_songs';"
    )

    await cursor.execute(check)
    res = await cursor.fetchall()

    if res == []:
        query = (
            "CREATE TABLE playlist_songs ("
            "p_id  VARCHAR(255),"
            "v_id  VARCHAR(255),"
            "PRIMARY KEY (p_id, v_id)," \
            "FOREIGN KEY (v_id) REFERENCES songs(id),"
            "FOREIGN KEY (p_id) REFERENCES playlists(id)"
            ");"
            )
        await cursor.execute(query)

        res = await cursor.fetchall()
        print(f"{cursor.statement}: {res}")
    else:
        print("table searches exists")

    await cursor.close()



async def drop_all():
    cursor = await cnx.cursor()

    query = (
        "SET FOREIGN_KEY_CHECKS = 0;"
        "DROP TABLE playlists;"
        "DROP TABLE songs;"
        "DROP TABLE playlist_songs;"
        "DROP TABLE searches;"
        "SET FOREIGN_KEY_CHECKS = 1;"
    )
    await cursor.execute(query)

    res = await cursor.fetchall()
    print(f"{cursor.statement}: {res}")

    await cursor.close()


async def add_song(video_id: str, title:str, searches: list[str]):
    cursor = await cnx.cursor()

    query = (
        "INSERT INTO songs(id, title)"
        "VALUES (%s, %s);" 
    )
    data = (video_id, title)

    try:
        await cursor.execute(query, data)
        await cnx.commit()
    except Exception as e:
        print("EXCEPTION: " + str(e))
        res = await cursor.fetchall()
        print(f"{cursor.statement}: {res}")

    await cursor.close()


    for i in searches:
        await add_search(i, video_id)




async def add_search(query: str, video_id: str):
    cursor = await cnx.cursor()

    sql_query = (
        "INSERT INTO searches (query, v_id)"
        "VALUES (%s, %s)"
    )
    data = (query, video_id)

    try:
        await cursor.execute(sql_query, data)
        await cnx.commit()
    except Exception as e:
        print("EXCEPTION: " + str(e))
        res = await cursor.fetchall()
        print(f"{cursor.statement}: {res}")

    await cursor.close()


async def search_song(query: str):
    cursor = await cnx.cursor()
    sql_query = (
        "SELECT songs.id, songs.title " # need to put spaces here
        "FROM searches "
        "JOIN songs ON searches.v_id = songs.id "
        "WHERE searches.query = %s;"
    )
    data = (query,)
    await cursor.execute(sql_query, data)

    res = await cursor.fetchall()
    if len(res) > 0:
        vid, name = res[0]
        print(f"id: {vid}, title: {name}")
    else:
        print("failed to find")

    await cursor.close()
    


async def add_playlist(playlist_id: str, title:str, songs: list[str]):
    cursor = await cnx.cursor()
    query = (
        "INSERT INTO playlists(id, title)"
        f"VALUES (%s, %s);"
        )
    data = (playlist_id, title)

    await cursor.execute(query, data)

    res = await cursor.fetchall()
    print(f"{cursor.statement}: {res}")

    query = (
        "INSERT INTO playlist_songs(p_id, v_id)"
        "VALUES (%s, %s);"
    )
    for i in songs:
        data = (playlist_id, i)
        try:
            await cursor.execute(query, data)
            # await cnx.commit()
        except Exception as e:
            print("EXCEPTION: " + str(e))
            res = await cursor.fetchall()
            print(f"{cursor.statement}: {res}")


    await cnx.commit()
    await cursor.close()