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


async def get_local_playlist_songs(guild_id, name: str) -> list[str]:
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

    if len(res > 0):
        return res[0]
    else:
        return []


async def get_lpl_autocomplete(query: str) -> list[str]:
    cnx = await get_connection()
    cursor = await cnx.cursor()
    sql_query = (
        "SELECT name "
        "FROM local_playlists "
        "WHERE name LIKE %s;"
    )
    data = (query,)
    print(f"searching {query}")
    await cursor.execute(sql_query, data)

    res = await cursor.fetchall()
    titles = []

    if len(res) > 0:
        titles = res[0]
        print(titles)
    else:
        print("failed to find")

    await cursor.close()
    await cnx.shutdown()
    
    return titles