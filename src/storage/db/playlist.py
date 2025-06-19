from .general import get_connection
import traceback


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