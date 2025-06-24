import json, asyncio, os
from typing import Any
from storage import db
from discord import ApplicationContext as actx
from network import ytHandler as yt
from models.enums import SongStatus


class Song:
    def __init__(self, title: str, id: str):
        self.id: str = id
        self.title: str = title
        self.status: SongStatus = SongStatus.SEARCHING_LOCAL


    @classmethod
    def search(cls, link: str='', query: str='' ) -> 'Song':
        # placeholder title
        if not query == '':
            title = query
        elif not link == '':
            title = link
        else:
            title = "???"
        inst = cls(title, '')

        # async grab info
        if not link == '' or not query == '':
            asyncio.create_task(inst.__ensure_song(link, query))

        return inst
    

    @classmethod
    def from_info(cls, title: str, id: str) -> 'Song':
        inst = cls(title, id)

        return inst
    

    async def __ensure_song(self, link: str, search: str):
        # get title, id
        self.id, self.title = await self.__find_info(link, search)

        if self.id == '':
            self.status = SongStatus.FAILED
            return
        
        # download
        if await self.__ensure_file():
            self.status = SongStatus.READY
        else:
            self.status = SongStatus.FAILED


    async def __find_info(self, link: str, search: str) -> tuple[str, str]:
        # title search:
        if not search == '':

            # db lookup
            vid, title = await db.search_song(search)

            if not vid == '':
                return vid, title
            
            # yt lookup
            else:
                self.status = SongStatus.SEARCHING
                vid, title = await asyncio.to_thread(yt.get_cache, search)
                
                await db.add_song(vid, title, [search])
                return vid, title
            
        # link search
        elif not link == '':
            # db lookup
            clean_link = yt.remove_playlist_from_link(link)
            vid = yt.get_id_from_link(clean_link)
            vid, title = await db.search_id(vid)
            
            if not title == '':
                return vid, title
            
            # yt lookup
            else:
                self.status = SongStatus.SEARCHING
                vid, title = await asyncio.to_thread(yt.get_cache, clean_link, is_link=True)
                await db.add_song(vid, title, [])
                return vid, title
        # we got empty somehow
        else:
            return '', ''


    async def __ensure_file(self) -> bool:
        filename = f'songs/{self.id}.mp3'
        if os.path.exists(filename):
            return True
        
        self.status = SongStatus.DOWNLOADING
        full_link = 'https://www.youtube.com/watch?v=' + self.id
        res = await asyncio.to_thread(yt.download, full_link, filename)

        if not res:
            self.status = SongStatus.FAILED
            return False
            
        return True


    def __str__(self) -> str:
        return self.title