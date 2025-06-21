from typing import Self
from storage import db
from models.song import Song


class LocalPlaylist:
    def __init__(self, name: str, gid: int, songs: list[Song] | None = None):
        self.title: str = name
        self.songs: list[Song] = songs if songs is not None else []
        self.gid = gid


    def get_content(self) -> list[tuple[str, str]]:
        content = []

        for i in range(len(self.songs)):
            content.append((f"{i}. ", self.songs[i].title))

        return content
    

    def get_links(self) -> list[str]:
        return ["https://www.youtube.com/watch?v=" + i.id for i in self.songs]
    

    def get_ids(self) -> list[str]:
        return [i.id for i in self.songs]


    async def save(self) -> bool:
        ids = self.get_ids()
        if ids == []:
            return False
        
        await db.add_local_playlist(self.gid, self.title, ids)

        return True


    async def load(self) -> Self:
        song_info = await db.get_local_playlist_songs(self.gid, self.title)
        for id, title in song_info:
            self.songs.append(Song.from_info(title, id))

        return self