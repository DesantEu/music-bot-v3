import asyncio
from datetime import datetime
import json
import os
from typing import Any
import discord
from playback.songQueue import Queue
from playback import player
from network import dcHandler as dc
from locales import bot_locale as loc
# from playback import nowPlaying as np

class Instance:
    def __init__(self, gid:int, prefix:str, bot:discord.Client):
        self.guildid: int = gid
        self.prefix: str = prefix
        self.queue = Queue()
        self.queue_messages: list[int] = []
        # self.player: np.Player
        # self.hasPlayer = False
        self.skipSkip = False
        self.song_start_time = datetime.now()
        self.pause_time = datetime.now()
        self.pos = 0
        self.current = -1
        self.volume = 1.0
        self.isPlaying = False
        self.isStopped = True
        self.isPaused = False
        self.vc: discord.VoiceClient
        self.bot = bot
        # self.rmlist: list[str] = []
        self.past_queues: list[Queue] = []

        if not self.load_from_disk():
            print(f"could not load instance {self.guildid} from disk")
            self.past_queues: list[Queue] = []
            self.rmlist: list[str] = []
            self.prefix: str = prefix
            # self.queue_messages: list[int] = []

        print(f"created instance {self.guildid}")

    def __del__(self):
        print(f"destroying instance for {self.guildid}")
        player.stop(self)
        asyncio.run(dc.leave(self))
        # await dc.leave(self)

        self.save_to_disk()
            


    async def update_queue(self):
        # delete old queue messages
        max_messages = 5
        if len(self.queue_messages) > max_messages:
            while True:
                self.queue_messages.pop(0)
                if len(self.queue_messages) <= max_messages:
                    break

        # update queue messages
        for i in self.queue_messages:
            # await dc.edit_status(i, self.queue_messages[i], self.queue)
            await dc.edit_long_content(i, [[f'{self.queue.index(i) + 1}. ', i.title] for i in self.queue])


    def update_now_playing(self):
        if self.queue.len() == 0:
            song_title = "..."
        else:
            # song_title = loc.now_playing + " " + self.queue[self.current].title
            song_title = f"{loc.now_playing} {self.current + 1}. {self.queue[self.current].title}"
        for i in self.queue_messages:
            asyncio.run_coroutine_threadsafe(dc.edit_long_smaller_title(i, song_title),
                                             asyncio.get_running_loop())


    def after_song(self, error):
        if error:
            try:
                with open("error_log.log", "w+") as file:
                    log = file.read()
                    log += f"[{datetime.now()}] [after_song]: '{error}'"
                    file.write(log)
            except Exception as e:
                print(f"WTF?!?!? {e}")
            return

        # avoid recursion when skipping
        if self.skipSkip:
            self.skipSkip = False
            return
        player.skip(self, afterSong=True)
        pass


    async def on_disconnect(self):
        player.stop(self)
        await dc.leave(self)
        print('got kicked, leaving')


    def hasVC(self) -> bool:
        try:
            self.vc
            return True
        except:
            return False

    def save_to_disk(self):
        with open(f"saves/{self.guildid}.json", "w+") as file:
            file.write(json.dumps(self.toJson()))

    def load_from_disk(self) -> bool:
        if not os.path.exists(f"saves/{self.guildid}.json"):
            print(f"no save for instance {self.guildid}")
            return False

        try:

            with open(f"saves/{self.guildid}.json", "r") as file:
                self.fromJson(file.read())
                return True

        except Exception as e:
            print(e)
            return False

    def toJson(self):
        rJson = {}
        rJson["prefix"] = self.prefix
        # rJson["queue_messages"] = self.queue_messages
        rJson["rmlist"] = self.rmlist
        rJson["past_queues"] = [i.toJsonStr() for i in self.past_queues]

        return rJson

    def fromJson(self, s: str):
        rJson: dict[str, Any] = json.loads(s)

        self.prefix = rJson["prefix"]
        # self.queue_messages = rJson["queue_messages"]
        self.rmlist = rJson["rmlist"]

        for i in rJson["past_queues"]:
            q = Queue()
            jsq: dict[str, str] = json.loads(i)
            for k in jsq.keys():
                q.append(jsq[k], k)

            self.past_queues.append(q)



