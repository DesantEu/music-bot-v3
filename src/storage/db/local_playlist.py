from .general import get_connection
import traceback


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

    for i in range(len(songs)):
        cnx = await get_connection()
        cursor = await cnx.cursor()

        query = (
            "SELECT id INTO @playlist_id FROM local_playlists WHERE name = %s;"
            "INSERT INTO local_playlist_songs (p_id, v_id, ind)"
            "VALUES (@playlist_id, %s, %s)"
        )
        data = (playlist_name, songs[i], i)
        try:
            print(f"inserting id {songs[i]}")
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


async def get_local_playlist_songs(guild_id, name: str) -> list[tuple[str, str]]:
    cnx = await get_connection()
    cursor = await cnx.cursor()

    query = (
        "SELECT songs.id, songs.title "
        "FROM local_playlists "
        "JOIN local_playlist_songs ON local_playlist_songs.p_id = local_playlists.id "
        "JOIN songs ON songs.id = local_playlist_songs.v_id "
        "WHERE local_playlists.name = %s "
        "AND local_playlists.g_id = %s "
        "ORDER BY local_playlist_songs.ind ASC"
    )
    data = (name, guild_id)

    await cursor.execute(query, data)
    res = await cursor.fetchall()
    print(res)
    
    await cursor.close()
    await cnx.shutdown()

    if len(res) > 0:
        return res
    else:
        return []


async def get_lpl_autocomplete(query: str, guild_id: int) -> list[str]:
    cnx = await get_connection()
    cursor = await cnx.cursor()
    mask = '%' + query + '%'
    sql_query = (
        "SELECT name "
        "FROM local_playlists "
        "WHERE name LIKE %s "
        "AND g_id = %s "
        "LIMIT 10"
    )
    data = (mask, guild_id)
    print(f"searching {query}")
    await cursor.execute(sql_query, data)

    res = await cursor.fetchall()
    titles = []

    if len(res) > 0:
        titles = [r[0] for r in res] # flatten
        print(titles)
    else:
        print("failed to find")

    await cursor.close()
    await cnx.shutdown()
    
    return titles


async def lpl_create():
    cnx = await get_connection()
    cursor = await cnx.cursor()
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
            "ind INT,"
            "PRIMARY KEY (p_id, v_id)," 
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


async def lpl_drop():
    cnx = await get_connection()
    cursor = await cnx.cursor()
    query = (
        "SET FOREIGN_KEY_CHECKS = 0;"

        "DROP TABLE local_playlists;"
        "DROP TABLE local_playlist_songs;"
        
        "SET FOREIGN_KEY_CHECKS = 1;"
    )
    await cursor.execute(query)