import traceback
from models.enums import PlayerStates
from .general import get_connection

async def save_state(guild_id: int, state: PlayerStates, current: int, song_time: str, vc_id: int, q_msg_id: int, qc_id: int) -> bool:
    cnx = await get_connection()
    cursor = await cnx.cursor()

    query = (
        "INSERT INTO savestates (g_id, state, current, song_time, vc_id, qm_id, qc_id) "
        "VALUES (%(g_id)s, %(state)s, %(current)s, %(song_time)s, %(vc_id)s, %(qm_id)s, %(qc_id)s) "
        "ON DUPLICATE KEY UPDATE "
        "state = %(state)s,"
        "current = %(current)s,"
        "song_time = %(song_time)s,"
        "vc_id = %(vc_id)s,"
        "qm_id = %(qm_id)s,"
        "qc_id = %(qc_id)s,"
        "saved_at = CURRENT_TIMESTAMP"
    )
    data = {'g_id':guild_id, 'state': int(state), 'current':current, 'song_time': song_time, 'vc_id':vc_id, 'qm_id': q_msg_id, 'qc_id': qc_id }

    try:
        print(f"saving state for: {guild_id}")
        print(f"state: {state}")
        print(f"current: {current}")
        print(f"song_time: {song_time}")
        print(f"vc: {vc_id}")
        await cursor.execute(query, data)
        await cnx.commit()
        print(f"{cursor.statement}: {await cursor.fetchall()}")
        res = True
    except Exception:
        traceback.print_exc()
        print(cursor.statement)
        await cnx.rollback()
        res = False
    finally:
        await cursor.close()
        await cnx.shutdown()
        return res
    

async def update_state(guild_id: int, status: PlayerStates):
    cnx = await get_connection()
    cursor = await cnx.cursor()
    
    query = (
        "INSERT INTO savestates (g_id, state) "
        "VALUES (%(g_id)s, %(state)s) "
        "ON DUPLICATE KEY UPDATE "
        "state = %(state)s,"
        "saved_at = CURRENT_TIMESTAMP"
    )
    data = {'g_id': guild_id, 'state': int(status)}
    try:
        print(f"updating state for: {guild_id} to {status}")
        await cursor.execute(query, data)
        await cnx.commit()
        print(f"{cursor.statement}: {await cursor.fetchall()}")
    except Exception:
        traceback.print_exc()
        print(cursor.statement)
        await cnx.rollback()
    finally:
        await cursor.close()
        await cnx.shutdown()


async def get_state(guild_id: int) -> tuple[PlayerStates, int, str, int, int, int] | None:
    cnx = await get_connection()
    cursor = await cnx.cursor()

    query = (
        "SELECT state, current, song_time, vc_id, qm_id, qc_id "
        "FROM savestates "
        "WHERE g_id = %s;"
    )
    data = (guild_id, )

    await cursor.execute(query, data)
    res = await cursor.fetchall()
    print(res)
    await cursor.close()
    await cnx.shutdown()

    if len(res) > 0:
        state, current, song_time, vc_id, qm_id, qc_id = res[0]
        state = PlayerStates(state)
        return (state, current, song_time, vc_id, qm_id, qc_id)
    else:
        return None


    