import asyncio
from models.song import Song
from models.enums import SongStatus
from storage import db
from models.queue import Queue


from network import ytHandler as yt

class Playlist:
    def __init__(self):
        self.title: str
        self.id: str
        self.songs: list[Song]

    
    @classmethod
    async def search(cls, query: str, queue: Queue) -> 'Playlist':
        # first try to find the playlist in the local db
        # if it exists, return it
        # else search on yt
        # block until we have the info

        id = yt.get_id_from_playlist_link(query)

        # search in db
        if query.startswith("https://"):
            songs = await db.get_playlist_songs(id)
        else:
            songs = await db.get_playlist_songs_by_name(query)
        # on local search success
        if not songs == []:
            inst = cls()
            inst.songs = [Song.from_info(title, id) for id, title in songs]
            return inst
        # else search on yt
        else:
            # get info from yt
            info = await asyncio.to_thread(yt.get_playlist_cache, id)
            if info[0] == '':
                raise Exception(f"Playlist with id {id} not found")
            
            inst = cls()
            inst.id = info[0]
            inst.title = info[1]
            inst.songs = [Song.from_info('playlist_song', song_id) for song_id in info[2]]
            # save to db
            asyncio.create_task(inst.wait_and_save(queue))

            return inst

        
    async def wait_and_save(self, queue: Queue) -> None:
        # wait for all songs to be ready
        ready = [SongStatus.READY, SongStatus.FAILED]
        while not all([s.status in ready for s in queue.q if s.id in self.get_ids()]):
            print("Waiting for songs to be ready...")
            await asyncio.sleep(0.3)
        
        # save to db
        await db.add_playlist(self.id, self.title, self.get_ids())


    def get_links(self) -> list[str]:
        return ["https://www.youtube.com/watch?v=" + i.id for i in self.songs]
    
    def get_ids(self) -> list[str]:
        return [i.id for i in self.songs]