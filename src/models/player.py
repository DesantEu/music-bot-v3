import asyncio
import discord
from discord import ApplicationContext as actx
from network import dcHandler as dc
from datetime import datetime
from .queue import Queue
from .song import Song
from .past_queue import PastQueue
from enum import Enum


class PlayerStates(Enum):
    PLAYING = 1
    PAUSED = 0
    STOPPED = -1

class Player:
    def __init__(self) -> None:
        self.queue = Queue()
        self.current = -1
        self.skipSkip = False

        self.song_start_time = datetime.now()
        self.pause_time = datetime.now()

        self.volume = 1.0

        self.vc: discord.VoiceClient
        self.state = PlayerStates.STOPPED


    async def play(self, ctx: actx, prompt: str | list[str]) -> bool:
        if type(prompt) is str:
            # handle empty prompts
            if prompt == '' and not self.state == PlayerStates.PAUSED:
                return False

            # check if the user is in a vc
            if not dc.isInVC(ctx.author):
                return False
            
            if "https://" in prompt:
                self.queue.append(Song(link=prompt))
            else:
                self.queue.append(Song(search=prompt))

            return True
        else:
            print(type(prompt))
            raise NotImplemented


    def resume(self) -> bool:
        self.state = PlayerStates.PLAYING
        return True


    def pause(self) -> bool:
        self.state = PlayerStates.PAUSED
        return True
    

    def stop(self) -> bool:
        had_vc = False
        # stop and leave vc
        if self.has_vc():
        # drop play.after
            had_vc = True
            self.skipSkip = True
            self.vc.stop()
        # else:
        #     return False

        self.state = PlayerStates.STOPPED
        self.current = -1
        asyncio.create_task(PastQueue.add())
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
    
    def play_from_queue(self, index: int):
        v_id = self.queue[index].id
        file = f'songs/{v_id}.mp3'

        self.vc.play(discord.FFmpegPCMAudio(file), after=self.__after_song)
        self.current = index
        self.update_now_playing() # hopefully this works
        self.resume()

    
    def update_now_playing(self):
        raise Exception("NOT OVERRIDDEN (update)")


    def has_vc(self) -> bool:
        # return False
        raise Exception("NOT OVERRIDDEN (vc)")



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



# async def play(ctx: actx, prompt:str, inst):
#     # handle empty prompts
#     if prompt == '' and not inst.isPaused:
#         await ctx.send_response(dc.reactions.fyou, ephemeral=True)
#         return

#     # check if the user is in a vc
#     if not dc.isInVC(ctx.author):
#         await ctx.send_response(loc.no_vc, ephemeral=True)
#         return -1


#     isSuccessful = -1

#     # handle links
#     if prompt.startswith('https://'):
#         # handle playlists
#         if 'list=' in prompt:
#             # isSuccessful = await cahe.find_link_play(ctx, yt.remove_playlist_from_link(prompt), inst)

#         # handle a single song
#         else:
#             isSuccessful = await cahe.find_link_play(ctx, prompt, inst)
#     # handle text search
#     else:
#         isSuccessful = await cahe.find_prompt_play(ctx, prompt, inst)

#     if not isSuccessful == 0:
#         return -1

#     # check vc again just to be sure
#     if not dc.isInVC(ctx.author):
#         await ctx.send_followup(loc.left_vc, ephemeral=True)
#         return -1
#     else:
#         await dc.join(ctx, inst)
#         if not inst.isPlaying:
#             play_from_queue(0, inst) # TODO: remove
