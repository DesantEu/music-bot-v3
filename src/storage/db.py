from mysql.connector.aio import connect
from mysql.connector.aio.abstracts import MySQLConnectionAbstract, MySQLCursorAbstract
import os
import traceback

async def get_connection() -> MySQLConnectionAbstract:
    cnx = await connect(
        host="mysql",
        user="root",
        password=os.environ["MYSQL_ROOT_PASSWORD"],
        connection_timeout=10000,
        database="discord"
    )
    return cnx

# TODO: def is_table(name, cursor)

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


async def track_guild(guild_id: int, name: str):
    cnx = await get_connection()
    cursor = await cnx.cursor()

    query = (
        "INSERT INTO guilds (id, name) "
        "VALUES (%(g_id)s, %(name)s) "
        "ON DUPLICATE KEY UPDATE name = %(name)s;"
    )
    # data = (guild_id, name, name)
    data = {'g_id': str(guild_id), 'name': name }
    print(f"trying to track (id: {guild_id}, name: {name})")
    print(f"q:{type(query)}\nd:{type(data)}\ng:{type(guild_id)}\nn:{type(name)}")
    
    try:
        await cursor.execute(query, data)
        await cnx.commit()
    except Exception:
        print(traceback.format_exc())
        # res = await cursor.fetchall()
        # print(f"{cursor.statement}: {res}")

    await cursor.close()
    await cnx.shutdown()


async def add_song(video_id: str, title:str, searches: list[str]):
    cnx = await get_connection()
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
    await cnx.shutdown()


    for i in searches:
        await add_search(i, video_id)


async def add_local_playlist(guild_id: int, playlist_name: str, songs: list[str]):
    cnx = await get_connection()
    cursor = await cnx.cursor()

    query = (
        # playlist entry:
        "INSERT IGNORE INTO local_playlists (name, g_id)"
        "VALUES (%(name)s, %(g_id)s);"
        # remember id
        "SELECT id INTO @playlist_id FROM local_playlists WHERE name = %(name)s;"
        # clear old playlist
        "DELETE FROM local_playlist_songs "
        "WHERE p_id = @playlist_id;"
    )
    # data = (name, guild_id, name)
    data = {'g_id': guild_id, 'name': playlist_name}

    await cursor.execute(query, data)
    await cnx.commit()
    await cursor.close()
    await cnx.shutdown()

    for song in songs:
        cnx = await get_connection()
        cursor = await cnx.cursor()

        query = (
            "SELECT id INTO @playlist_id FROM local_playlists WHERE name = %s;"
            "INSERT INTO local_playlist_songs (p_id, v_id)"
            "VALUES (@playlist_id, %s)"
        )
        data = (playlist_name, song)
        try:
            print(f"inserting id {song}")
            await cursor.execute(query, data)
            await cnx.commit()
        except Exception:
            traceback.print_exc()
        finally:
            await cursor.close()
            await cnx.shutdown()



async def get_local_playlists(guild_id: int):
    cnx = await get_connection()
    cursor = await cnx.cursor()

    query = (
        "SELECT name"
        "FROM local_playlists "
        "WHERE g_id = %s"
    )
    data = (guild_id,)

    await cursor.execute(query, data)
    res = await cursor.fetchall()
    print(res)
    await cursor.close()
    await cnx.shutdown()

    return res


async def get_local_playlist_songs(guild_id, name: str):
    cnx = await get_connection()
    cursor = await cnx.cursor()

    query = (
        "SELECT songs.id, songs.title "
        "FROM local_playlists "
        "JOIN local_playlist_songs ON local_playlist_songs.p_id = local_playlists.id "
        "JOIN songs ON songs.id = local_playlist_songs.v_id "
        "WHERE local_playlists.name = %s "
        "AND local_playlists.g_id = %s "
    )
    data = (name, guild_id)

    await cursor.execute(query, data)
    res = await cursor.fetchall()
    print(res)
    
    await cursor.close()
    await cnx.shutdown()

    return res


async def add_search(query: str, video_id: str):
    cnx = await get_connection()
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
    await cnx.shutdown()


async def search_song(query: str) -> tuple[str, str]:
    cnx = await get_connection()
    cursor = await cnx.cursor()
    sql_query = (
        "SELECT songs.id, songs.title " # need to put spaces here
        "FROM searches "
        "JOIN songs ON searches.v_id = songs.id "
        "WHERE searches.query = %s;"
    )
    data = (query,)
    print(f"searching {query}")
    await cursor.execute(sql_query, data)

    res = await cursor.fetchall()
    vid = ''
    name = ''

    if len(res) > 0:
        vid, name = res[0]
        print(f"id: {vid}, title: {name}")
    else:
        print("failed to find")

    await cursor.close()
    await cnx.shutdown()
    
    return str(vid), str(name)
    


async def add_playlist(playlist_id: str, title:str, songs: list[str]):
    cnx = await get_connection()
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
        except Exception as e:
            print("EXCEPTION: " + str(e))
            res = await cursor.fetchall()
            print(f"{cursor.statement}: {res}")


    await cnx.commit()
    await cursor.close()
    await cnx.shutdown()