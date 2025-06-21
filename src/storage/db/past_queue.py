from .general import get_connection
import traceback


async def past_queue_save(guild_id: int, song_ids: list[str]) -> bool:
    cnx = await get_connection()
    cursor = await cnx.cursor()

    try:
        # shift previous ones
        await cursor.execute(
            "UPDATE past_queues SET ind = ind + 1 WHERE g_id = %s ORDER BY ind DESC; " ,
            (guild_id, )
        )
        # add new
        await cursor.execute(
            "INSERT INTO past_queues (g_id, ind) VALUES (%s, 1);",
            (guild_id, )
        )
        # get new queue id
        await cursor.execute("SELECT LAST_INSERT_ID(); ")
        new_id = (await cursor.fetchone())
        if new_id is not None: new_id = new_id[0]

        # add songs
        values_template = ', '.join(["(%s, %s, %s)"] * len(song_ids))
        values_data = []

        for ind, vid in enumerate(song_ids):
            values_data.extend([new_id, vid, ind]
                            )
        await cursor.execute((
            "INSERT INTO past_queue_songs (q_id, s_id, ind) "
            f"VALUES {values_template};"),
            values_data
        )
        # delete old queues
        await cursor.execute(
            "DELETE FROM past_queues WHERE g_id = %s AND ind > 10;",
            (guild_id, )
        )


        print(f"inserting queue {song_ids}")
        await cnx.commit()
        print(f"{cursor.statement}: {await cursor.fetchall()}")
        return True
    except Exception:
        traceback.print_exc()
        print(cursor.statement)
        await cnx.rollback()
        return False
    finally:
        await cursor.close()
        await cnx.shutdown()


async def past_queue_get(guild_id: int, index: int) -> list[tuple[str, str]]:
    cnx = await get_connection()
    cursor = await cnx.cursor()

    query = (
        "SELECT songs.id, songs.title "
        "FROM past_queues "
        "JOIN past_queue_songs ON past_queue_songs.q_id = past_queues.id "
        "JOIN songs ON songs.id = past_queue_songs.s_id "
        "WHERE past_queues.g_id = %s "
        "AND   past_queues.ind = %s "
        "ORDER BY past_queue_songs.ind ASC;"
    )
    data = (guild_id, index)


    await cursor.execute(query, data)
    res = await cursor.fetchall()

    await cursor.close()
    await cnx.shutdown()

    if len(res) > 0:
        return res
    else:
        return []
    

async def past_queue_get_all(guild_id: int) -> dict[int, list[tuple[str, str]]]:
    cnx = await get_connection()
    cursor = await cnx.cursor()

    query = (
        "SELECT past_queues.ind, songs.id, songs.title "
        # "SELECT past_queues.ind, past_queue_songs.ind, songs.id, songs.title "
        "FROM past_queues "
        "JOIN past_queue_songs ON past_queue_songs.q_id = past_queues.id "
        "JOIN songs ON songs.id = past_queue_songs.s_id "
        "WHERE past_queues.g_id = %s "
        "ORDER BY past_queues.ind, past_queue_songs.ind;"
    )
    data = (guild_id, )

    await cursor.execute(query, data)
    res = await cursor.fetchall()
    
    await cursor.close()
    await cnx.shutdown()
    
    queues: dict[int, list[tuple[str, str]]] = {}
    for qi, vid, title in res:
        if not qi in queues.keys():
            queues[qi] = []

        queues[qi].append((vid, title))

    return queues


