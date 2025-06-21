from typing import Self
import discord
from locales import bot_locale as loc
from network import dcHandler as dc
from models.song import Song
from storage import db

class PastQueue:
    def __init__(self, guild_id: int, songs: list[Song] | None = None):
        self.gid = guild_id
        self.songs: list[Song] = songs if songs is not None else []


    async def load(self, index: int) -> Self:
        res = await db.past_queue_get(self.gid, index)
        for vid, title in res:
            self.songs.append(Song.from_info(title, vid))
        return self
    
    async def get_content(self) -> list[tuple[str, str]]:
        content: list[tuple[str, str]] = []
        data = await db.past_queue_get_all(self.gid)

        for i in data.keys():
            content.append((f"{i}.", ' '))

            for _, (_, title) in enumerate(data[i]):
                content.append(('> ', title))

        return content
    

    def get_ids(self) -> list[str]:
        return [i.id for i in self.songs]


    def get_links(self) -> list[str]:
        return ["https://www.youtube.com/watch?v=" + i.id for i in self.songs]


    async def save(self) -> bool:
        ids = self.get_ids()
        if ids == []:
            return False
        
        return await db.past_queue_save(self.gid, ids)
    