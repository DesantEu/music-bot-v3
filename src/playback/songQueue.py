import json

class Song:
    def __init__(self, link, title, instaplay_message=''):
        self.link = link
        self.title = title
        self.length = 0 # TODO
        self.instaplay_message = instaplay_message
        self.can_instaplay = False if instaplay_message == '' else True
    
class Queue:
    def __init__(self):
        self.q: list[Song] = []

    def __getitem__(self, key) -> Song:
        return self.q[key]
    
    def append(self, link, title, instaplay_message=''):
        self.q.append(Song(link, title, instaplay_message))

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

    def copy(self):
        q = Queue()
        for i in self.q.copy():
            q.append(i.link, i.title)
        return q

    def __str__(self) -> str:
        return '\n'.join([f'{self.q.index(i) + 1}. ' + i.title for i in self.q])

    def toStrWithCurrent(self, current) -> str:
        return '\n'.join([f"{'> ' if current == self.q.index(i) else '  '}" + f'{self.q.index(i) + 1}. ' + i.title for i in self.q])

    def toContent(self):
        return [[f'{self.q.index(i) + 1}. ', i.title] for i in self.q]

    def toJsonStr(self) -> str:
        rJson = {}
        for i in self.q:
            rJson[i.title] = i.link

        return json.dumps(rJson)

