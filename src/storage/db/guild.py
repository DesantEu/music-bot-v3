from .general import get_connection
import traceback


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