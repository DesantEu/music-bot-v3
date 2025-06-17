import json
from typing import Any


class CachedSong:
    def __init__(self, link: str='', title: str='', searches: list[str]=[], is_playlist=False):
        self.link = link
        self.title = title
        self.searches = searches
        self.is_playlist = is_playlist

    def toJson(self):
        rJson = {}
        rJson['link'] = self.link
        rJson['title'] = self.title
        rJson['searches'] = self.searches
        rJson['is_playlist'] = self.is_playlist

        return rJson

    def fromJson(self, o: dict[str, Any]):
        self.link = o['link']
        self.title = o['title']
        self.searches = o['searches']
        if 'is_playlist' in o:
            self.is_playlist = o['is_playlist']
        else:
            self.is_playlist = False

    def __str__(self) -> str:
        return json.dumps(self.toJson())