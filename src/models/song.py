import json, asyncio, os
from typing import Any
from enum import Enum
from storage import db
from discord import ApplicationContext as actx
from network import ytHandler as yt

class SongStatus(Enum):
    READY = 0
    SEARCHING = 1
    SEARCHING_LOCAL = 2
    DOWNLOADING = 3
    FAILED = -1

class Song:
    def __init__(self, link: str='', search: str='' , ctx: actx | None = None):
        self.id: str
        self.title: str
        self.status: SongStatus = SongStatus.SEARCHING_LOCAL
        silent = ctx is actx

        # placeholder title
        if not search == '':
            self.title = search
        elif not link == '':
            self.title = link
        else:
            self.title = "???"

        # async grab info
        asyncio.create_task(self.__ensure_song(link, search, silent))

    
    async def __ensure_song(self, link: str, search: str, silent: bool):
        # get title, id
        self.id, self.title = await self.__find_info(link, search, silent)

        if self.id == '':
            self.status = SongStatus.FAILED
            return
        
        # download
        downloaded = await self.__ensure_file()
        if not downloaded:
            self.status = SongStatus.FAILED
            return

        self.status = SongStatus.READY


    async def __find_info(self, link: str, search: str, silent: bool) -> tuple[str, str]:
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
            vid = yt.remove_playlist_from_link(link)
            clean_link = yt.get_id_from_link(vid)
            vid, title = await db.search_id(vid)
            
            if not vid == '':
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


        # if not search == '':
        #     # vid, title = await db.search_song(search)
        #     if vid == '' or title == '':
        #         self.status = SongStatus.SEARCHING
        #         # TODO: YT lookup and download
        #     else:
        #         self.title = title
        #         self.id = vid
        #         self.status = SongStatus.READY


    async def __ensure_file(self) -> bool:
        filename = f'songs/{self.id}.mp3'
        if not os.path.exists(filename):
            self.status = SongStatus.DOWNLOADING
            full_link = 'https://www.youtube.com/watch?v=' + self.id

            res = await asyncio.to_thread(yt.download, full_link, filename)
            if not res == 0:
                return False
            
        return True


    def __str__(self) -> str:
        return self.title