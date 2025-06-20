import json
from models.song import Song, SongStatus
from network import dcHandler as dc
    
class Queue:
    def __init__(self):
        self.q: list[Song] = []

    def __getitem__(self, key: int) -> Song:
        return self.q[key]
    
    def append(self, song: Song):
        self.q.append(song)

    def pop(self, index) -> str:
        if index.startswith('-') or not index.isdigit() or self.len() == 0 or index == '':
            return ''

        index = int(index)
        if index < 1 or index > self.len():
            return ''

        song = self.q.pop(index - 1).title
        return song

    def index(self, elem) -> int:
        return self.q.index(elem)

    def index_title(self, elem) -> int:
        for i in self.q:
            if i.title == elem:
                return self.index(i)
        return -1
            

    def len(self):
        return len(self.q)

    def clear(self):
        self.q = []

    # def copy(self):
    #     q = Queue()
    #     for i in self.q.copy():
    #         q.append(i.id, i.title)
    #     return q

    def __str__(self) -> str:
        return '\n'.join([f'{self.q.index(i) + 1}. ' + i.title for i in self.q])

    def toStrWithCurrent(self, current) -> str:
        return '\n'.join([f"{'> ' if current == self.q.index(i) else '  '}" + f'{self.q.index(i) + 1}. ' + i.title for i in self.q])

    def toContent(self) -> list[tuple[str,str]]:
        # return [[f'{self.q.index(i) + 1}. ', i.title] for i in self.q]
        content = []
        for song in self.q:
            if song.status == SongStatus.READY:
                status = f'{self.q.index(song) + 1}. '
            elif song.status == SongStatus.SEARCHING_LOCAL:
                status = dc.reactions.folder
            elif song.status == SongStatus.SEARCHING:
                status = dc.reactions.search
            elif song.status == SongStatus.FAILED:
                status = dc.reactions.cross
            elif song.status == SongStatus.DOWNLOADING:
                status = dc.reactions.down_arrow
            content.append((status, song.title))

        return content
    
    def get_IDs(self) -> list[str]:
        return [i.id for i in self.q]

    # def toJsonStr(self) -> str:
    #     rJson = {}
    #     for i in self.q:
    #         rJson[i.title] = i.link

    #     return json.dumps(rJson)

