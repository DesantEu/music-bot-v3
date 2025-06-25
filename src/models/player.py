import asyncio
import discord
from discord import ApplicationContext as actx
from network import dcHandler as dc
from datetime import datetime, timedelta
from .queue import Queue
from .song import Song
from .past_queue import PastQueue
from .enums import PlayerStates


class Player:
    def __init__(self) -> None:
        self.queue = Queue()
        self.current = -1
        self.skipSkip = False

        self.song_start_time = datetime.now()
        self.pause_time = datetime.now()

        self.volume = 1.0

        self.vc: discord.VoiceClient
        self.guildid: int
        self.state = PlayerStates.STOPPED


    async def play(self, ctx: actx | None, prompt: str | list[str]) -> bool:
        if type(prompt) is str:
            # handle empty prompts
            if prompt == '' and not self.state == PlayerStates.PAUSED:
                return False

            # check if the user is in a vc
            if ctx is not None and not dc.isInVC(ctx.author):
                return False
            
            if "https://" in prompt:
                self.queue.append(Song.search(link=prompt))
            else:
                self.queue.append(Song.search(query=prompt))

            return True
        else:
            for song in prompt:
                await self.play(ctx, song)
                
            return True


    def resume(self) -> bool:
        self.state = PlayerStates.PLAYING
        return True


    def pause(self) -> bool:
        self.state = PlayerStates.PAUSED
        return True
    
    async def remove(self, query: str) -> bool:
        if self.queue.len() == 0 or not self.has_vc():
            return False
        
        success = False
        indeces = self.__parse_remove(query)
        current_reduce = 0
        skip_later = self.current + 1 in indeces

        # reduce self.current if we remove anything before it
        for i in indeces:
            if i <= self.current + 1:
                current_reduce += 1

            # idk???
            res = self.queue.pop(str(i))
            if not res == '':
                # stop if queue is empty
                if self.queue.len() == 0:
                    await self.stop()
                success = True

        self.current -= current_reduce

        # move to a song before and skip to the one after it
        # if we removed what was playing ATM
        if skip_later:
            # self.current -= 1
            self.skip()
        else:
            self.update_now_playing()

        return success

    

    async def stop(self) -> bool:
        """ Stops the player, clears the queue and leaves the voice channel if it was connected.
        Gets called pretty much any time the bot is expected to stop playing music.
        (dc, stop, clear, etc.)
        Returns True if the player was connected to a voice channel, False otherwise.
        """
        had_vc = False
        # stop and leave vc
        if self.has_vc():
        # drop play.after
            had_vc = True
            self.skipSkip = True
            self.vc.stop()

        await self.save()

        self.state = PlayerStates.STOPPED
        self.current = -1
        self.queue.clear()

        return had_vc


    def skip(self, num='', afterSong=False) -> bool:
        if not self.has_vc() or self.queue.len() == 0:
            return False
        
        # handle numbers:
        if not num == '':
            try:
                num = int(num)
            except:
                return False

            if num < 0 or num > self.queue.len():
                return False
            
            if num == 0:
                next = 0
            else:
                next = num - 1
        # skip no number
        else:
            next = self.current + 1
            # roll over forward
            if next >= self.queue.len():
                next = 0

        # drop play.after to avoid recursive skipping
        if self.vc.is_playing():
            if not afterSong:
                self.skipSkip = True
            self.vc.stop()

        self.play_from_queue(next)
        return True
    

    def play_from_queue(self, index: int, start: str | timedelta = "00:00:00"):
        v_id = self.queue[index].id
        file = f'songs/{v_id}.mp3'

        if not isinstance(start, timedelta):
            h, m, s = map(int, start.split(":"))
            delta = timedelta(hours=h, minutes=m, seconds=s)
        else:
            delta = start

        print(f"Playing song {index} from queue: {self.queue[index].title} (start: {start})")

        self.vc.play(discord.FFmpegPCMAudio(file, before_options=f"-ss {start}", options='-f s16le')
                     , after=self.__after_song)
        self.state = PlayerStates.PLAYING

        self.song_start_time = datetime.now() - delta
        self.current = index
        self.update_now_playing() # hopefully this works
        self.resume()


    def get_delta(self, time: datetime) -> str:
        delta = datetime.now() - time
        total = int(delta.total_seconds())
        h, rem = divmod(total, 3600)
        m, s = divmod(rem, 60)
        return f"{h:02}:{m:02}:{s:02}"

    
    def update_now_playing(self):
        raise Exception("NOT OVERRIDDEN (update)")


    async def save(self) -> bool:
        raise Exception("NOT OVERRIDDEN (save)")

    def has_vc(self) -> bool:
        # return False
        raise Exception("NOT OVERRIDDEN (vc)")


    def __parse_remove(self, query: str) -> list[int]:
        removes = query.split(' ')
        max = self.queue.len()

        # do unreasonable transformations so you can bulk remove better
        # get deletion indeces from whatever garbage the user gives
        indeces = []

        for i in removes:
            # ignore negatives from spawn
            if i.startswith('-'):
                continue

            # handle ranges
            if '-' in i:
                start = -1
                end = -1

                splits = i.split('-')

                # safety measures
                # idk how that could happen but anyway
                if len(splits) == 1:
                    continue
                # only pick (1-25)-123
                try:
                    start = int(splits[0])
                    end = int(splits[1])
                    if end > max:
                        end = max
                # if letters are thrown in the sequence
                except:
                    continue

                # yea this would happen somehow
                if end < start:
                    continue

                for ind in range(start, end+1):
                    if ind > max:
                        continue

                    if not ind in indeces:
                        indeces.append(ind)

            # handle single numbers
            else:
                # parse int of course
                try:
                    ind = int(i)
                    if ind > max:
                        continue

                    if not i in indeces:
                        indeces.append(ind)
                # letters detected here
                except:
                    continue

        # ensure they are unique
        temp = []
        for i in indeces:
            if not i in temp:
                temp.append(i)
        indeces = temp

        # reverse and delete from end cuz indeces change and shit
        indeces = sorted(indeces, reverse=True)
        return indeces


    def __after_song(self, error):
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
        self.skip(afterSong=True)
