from .general import get_connection


async def add_song(video_id: str, title:str, searches: list[str]):
    cnx = await get_connection()
    cursor = await cnx.cursor()

    query = (
        "INSERT IGNORE INTO songs(id, title)"
        "VALUES (%s, %s);" 
    )
    data = (video_id, title)

    try:
        print(f"db: adding song {title}")
        await cursor.execute(query, data)
        await cnx.commit()
    except Exception as e:
        print("EXCEPTION: " + str(e))
        res = await cursor.fetchall()
        print(f"{cursor.statement}: {res}")

    await cursor.close()
    await cnx.shutdown()

    for i in searches: # TODO: make a normal request
        await add_search(i, video_id)


async def add_search(query: str, video_id: str):
    cnx = await get_connection()
    cursor = await cnx.cursor()

    sql_query = (
        "INSERT INTO searches (query, v_id)"
        "VALUES (%(query)s, %(v_id)s)"
        "ON DUPLICATE KEY UPDATE v_id = %(v_id)s;"

    )
    data = {'query':query, 'v_id': video_id}

    try:
        print(f"db: adding search {query}")
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
        "WHERE searches.query = %(query)s OR songs.title = %(query)s"
    )
    data = {'query': query}
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


async def search_id(video_id: str) -> tuple[str, str]:
    cnx = await get_connection()
    cursor = await cnx.cursor()
    sql_query = (
        "SELECT id, title " # need to put spaces here
        "FROM songs "
        "WHERE id = %s;"
    )
    data = (video_id,)
    print(f"searching {video_id}")
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


async def get_song_autocomplete(query: str) -> list[str]:
    cnx = await get_connection()
    cursor = await cnx.cursor()
    mask = '%' + query + '%'
    sql_query = (
        "SELECT DISTINCT songs.title "
        "FROM searches "
        "JOIN songs ON songs.id = searches.v_id "
        "WHERE searches.query LIKE %(mask)s OR songs.title LIKE %(mask)s OR songs.id = %(query)s"
        "LIMIT 10"
    )
    data = {'mask': mask, 'query': query}
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