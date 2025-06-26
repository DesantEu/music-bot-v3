from .general import get_connection
import traceback


async def add_playlist(playlist_id: str, title:str, songs: list[str]):
    cnx = await get_connection()
    cursor = await cnx.cursor()

    query = (
        # playlist entry:
        "INSERT IGNORE INTO playlists (id, title)"
        "VALUES (%(p_id)s, %(title)s);"
        # clear old playlist
        "DELETE FROM playlist_songs "
        "WHERE p_id = %(p_id)s;"
    )
    # data = (name, guild_id, name)
    data = {'p_id': playlist_id, 'title': title}

    await cursor.execute(query, data)
    await cnx.commit()
    await cursor.close()
    await cnx.shutdown()

    # add songs
    for i in range(len(songs)):
        cnx = await get_connection()
        cursor = await cnx.cursor()

        query = (
            "INSERT INTO playlist_songs (p_id, v_id, ind)"
            "VALUES (%s, %s, %s)"
        )
        data = (playlist_id, songs[i], i)
        try:
            print(f"inserting id {songs[i]}")
            await cursor.execute(query, data)
            await cnx.commit()
        except Exception:
            traceback.print_exc()
        finally:
            await cursor.close()
            await cnx.shutdown()



async def get_playlist_songs(playlist_id: str) -> list[tuple[str, str]]:
    """returns a list of tuples (song_id, song_title) for the given playlist_id"""
    cnx = await get_connection()
    cursor = await cnx.cursor()

    query = (
        "SELECT songs.id, songs.title "
        "FROM playlists "
        "JOIN playlist_songs ON playlist_songs.p_id = playlists.id "
        "JOIN songs ON songs.id = playlist_songs.v_id "
        "WHERE playlists.id = %s "
        "ORDER BY playlist_songs.ind ASC"
    )
    data = (playlist_id,)

    await cursor.execute(query, data)
    res = await cursor.fetchall()
    print(res)
    
    await cursor.close()
    await cnx.shutdown()

    if len(res) > 0:
        return res
    else:
        return []