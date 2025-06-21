from mysql.connector.aio import connect
from mysql.connector.aio.abstracts import MySQLConnectionAbstract
import os


async def get_connection() -> MySQLConnectionAbstract:
    cnx = await connect(
        host="mysql",
        user="root",
        password=os.environ["MYSQL_ROOT_PASSWORD"],
        connection_timeout=10000,
        database="discord"
    )
    return cnx

async def ensure_tables():
    cnx = await get_connection()
    cursor = await cnx.cursor()

    # guild tracker

    check = (
        "SHOW TABLES LIKE 'guilds';"
    )

    await cursor.execute(check)
    res = await cursor.fetchall()

    if res == []:
        query = (
            "CREATE TABLE guilds ("
            "id    BIGINT UNSIGNED PRIMARY KEY,"
            "name  VARCHAR(255)"
            ");"
            )
        await cursor.execute(query)

        res = await cursor.fetchall()
        print(f"{cursor.statement}: {res}")
    else:
        print("table guilds exists")


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

    # local playlists

    check = (
        "SHOW TABLES LIKE 'local_playlists';"
    )

    await cursor.execute(check)
    res = await cursor.fetchall()

    if res == []:
        query = (
            "CREATE TABLE local_playlists ("
            "id   INT AUTO_INCREMENT PRIMARY KEY,"
            "name VARCHAR(255) UNIQUE,"
            "g_id  BIGINT UNSIGNED,"
            "FOREIGN KEY (g_id) REFERENCES guilds(id)"
            ");"
            )
        await cursor.execute(query)

        res = await cursor.fetchall()
        print(f"{cursor.statement}: {res}")
    else:
        print("table local_playlists exists")


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
            "query VARCHAR(255) UNIQUE,"
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
            "PRIMARY KEY (p_id, v_id)," 
            "FOREIGN KEY (v_id) REFERENCES songs(id),"
            "FOREIGN KEY (p_id) REFERENCES playlists(id)"
            ");"
            )
        await cursor.execute(query)

        res = await cursor.fetchall()
        print(f"{cursor.statement}: {res}")
    else:
        print("table playlist_songs exists")


    # local playlist songs many to many

    check = (
        "SHOW TABLES LIKE 'local_playlist_songs';"
    )

    await cursor.execute(check)
    res = await cursor.fetchall()

    if res == []:
        query = (
            "CREATE TABLE local_playlist_songs ("
            "p_id  INT,"
            "v_id  VARCHAR(255),"
            "PRIMARY KEY (p_id, v_id)," \
            "FOREIGN KEY (v_id) REFERENCES songs(id),"
            "FOREIGN KEY (p_id) REFERENCES local_playlists(id)"
            ");"
            )
        await cursor.execute(query)

        res = await cursor.fetchall()
        print(f"{cursor.statement}: {res}")
    else:
        print("table local_playlist_songs exists")


    # past queues


    check = (
        "SHOW TABLES LIKE 'past_queues';"
    )

    await cursor.execute(check)
    res = await cursor.fetchall()

    if res == []:
        query = (
            "CREATE TABLE past_queues ("
            "id     INT AUTO_INCREMENT PRIMARY KEY,"
            "ind    INT,"
            "g_id   BIGINT UNSIGNED,"
            "UNIQUE (g_id, ind),"
            "FOREIGN KEY (g_id) REFERENCES guilds(id)"
            ");"
            )
        await cursor.execute(query)

        res = await cursor.fetchall()
        print(f"{cursor.statement}: {res}")
    else:
        print("table past_queues exists")


    # past queue songs


    check = (
        "SHOW TABLES LIKE 'past_queue_songs';"
    )

    await cursor.execute(check)
    res = await cursor.fetchall()

    if res == []:
        query = (
            "CREATE TABLE past_queue_songs ("
            "q_id   INT,"
            "s_id   VARCHAR(255),"
            "ind    INT,"
            "PRIMARY KEY (q_id, ind),"
            "FOREIGN KEY (q_id) REFERENCES past_queues(id) ON DELETE CASCADE,"
            "FOREIGN KEY (s_id) REFERENCES songs(id)"
            ");"
            )
        await cursor.execute(query)

        res = await cursor.fetchall()
        print(f"{cursor.statement}: {res}")
    else:
        print("table local_playlist_songs exists")



    await cursor.close()
    await cnx.shutdown()


async def drop_all():
    cnx = await get_connection()
    cursor = await cnx.cursor()

    query = (
        "SET FOREIGN_KEY_CHECKS = 0;"

        "DROP TABLE songs;"
        "DROP TABLE playlists;"
        "DROP TABLE playlist_songs;"
        "DROP TABLE local_playlists;"
        "DROP TABLE local_playlist_songs;"
        "DROP TABLE searches;"
        "DROP TABLE guilds;"
        
        "SET FOREIGN_KEY_CHECKS = 1;"
    )
    await cursor.execute(query)

    res = await cursor.fetchall()
    print(f"{cursor.statement}: {res}")

    await cursor.close()
    await cnx.shutdown()