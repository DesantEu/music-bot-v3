from datetime import datetime
import discord
import asyncio
from models.enums import PlayerStates
from models.past_queue import PastQueue
from models.player import Player
from models.song import SongStatus
from network import dcHandler as dc
from locales import bot_locale as loc
from discord import ApplicationContext as actx
from storage import db


class Instance(Player):
    def __init__(self, gid:int, bot: discord.Client):
        super().__init__()
        self.guildid: int = gid
        self.queue_message: int = 0
        self.queue_tracker = None

        self.bot = bot

        print(f"created instance {self.guildid}")


    async def play(self, ctx: actx | None, prompt: str | list[str]) -> bool:
        if ctx is not None:
            if not dc.isInVC(ctx.user):
                return False
            await self.join(ctx)

        play_success = await super().play(ctx, prompt)
        if not play_success:
            return False
        # send queue
        if self.queue_message == 0:
            await self.send_queue(ctx)
        # track song status
        if self.queue_tracker is None or self.queue_tracker.done():
            self.queue_tracker = asyncio.create_task(self.track_queue())
        return play_success



    async def send_queue(self, ctx: actx | None) -> int:
        if self.queue.len() == 0 or ctx is None:
            return -1

        song_title = self.__get_now_playing()
        content = self.queue.toContent()
        emb = await dc.send_long(loc.queue, song_title, content, ctx, respond=False)
        self.queue_message = emb

        return emb
    

    async def track_queue(self):
        ready_states = [SongStatus.READY, SongStatus.FAILED]
        # wait for ready
        while not all(song.status in ready_states for song in self.queue):
            if not self.queue_message == -1:
                await self.update_queue_embed()
            await asyncio.sleep(1)
            
        # on ready:
        await self.update_queue_embed()
        # start playing
        if self.current == -1:
            while not self.has_vc():
                await asyncio.sleep(0.2)
            self.play_from_queue(0)


    async def update_queue_embed(self):
        content = self.queue.toContent()
        await dc.edit_long_content(self.queue_message, content)


    def update_now_playing(self):
        song_title = self.__get_now_playing()

        asyncio.run_coroutine_threadsafe(
            dc.edit_long_smaller_title(self.queue_message, song_title),
            self.bot.loop)
        

    def has_vc(self) -> bool:
        try:
            self.vc
            return True
        except:
            return False
        

    def __get_now_playing(self) -> str:
        if self.queue.len() == 0:
            song_title = "..."
        else:
            if self.current == -1:
                song_title = "ща ща ща"
            else:
                song_title = f"{loc.now_playing} {self.current + 1}. {self.queue[self.current].title}"
        return song_title


    async def join(self, ctx: actx) -> bool:
        try:
            # connect if not yet connected
            if not self.has_vc():
                self.vc = await ctx.user.voice.channel.connect()
                return True
            # move to other channel maybe
            if not self.vc.channel == ctx.user.voice.channel:
                await self.vc.move_to(ctx.user.voice.channel)
            return True
        except Exception as e:
            print(f"exception caught: {e}")
            return False


    async def leave(self) -> bool:
        try:
            if not self.has_vc():
                return False

            self.vc.cleanup()
            await self.vc.disconnect()
            del(self.vc)

            return True
        except Exception as e:
            print(f'exception leaving: {e}')

            return False


    async def on_disconnect(self):
        self.stop()
        await self.leave()
        if not self.queue_message == -1:
            self.update_now_playing()
            await self.update_queue_embed()
        print('got kicked, leaving')

    
    async def save(self) -> bool:
        print(f"saving instance {self.guildid}", flush=True)
        # save time
        checkpoint = self.get_delta(self.song_start_time)

        # save the queue
        await PastQueue(self.guildid, self.queue.q).save()

        # if we are saving a stopped bot (if the bot was stopped and shut down)
        # only update status, leave state tha save
        # this makes it only so the bot doesnt rejoin
        if self.state == PlayerStates.STOPPED:
            print(f"{self.guildid}: saving stopped state")
            await db.update_state(self.guildid, self.state)
            return True

        # ensure we do have a vc
        vc_id = 0
        if self.has_vc() \
        and (type(self.vc.channel) is discord.channel.VoiceChannel \
        or type(self.vc.channel) is discord.channel.StageChannel):
            vc_id = int(self.vc.channel.id)

        # ensure we do have a queue message in a channel
        qc_id = 0
        if self.queue_message > 0:
            message = dc.long_messages[self.queue_message].message
            print(type(message))
            if type(message) is discord.Message:
                qc_id = message.channel.id

        return await db.save_state(self.guildid, self.state, self.current, checkpoint, vc_id, self.queue_message, qc_id)


    async def restore(self) -> bool:
        print(f"restoring session for {self.guildid}")

        res = await db.get_state(self.guildid)
        if res is None:
            return False
        print(f"{self.guildid}: got state")
        
        state, current, song_time, vc_id, qm_id, qc_id = res
        guild = self.bot.get_guild(self.guildid)
        if guild is None:
            return False
        print(f"{self.guildid}: got guild")
        
        # try restore queue message
        if qc_id > 0:
            qm_channel = guild.get_channel(qc_id) # need channel
            if type(qm_channel) is discord.TextChannel:
                # create placeholder long message
                print(f"{self.guildid}: creating queue message")
                self.queue_message = qm_id
                dc.long_messages[qm_id] = dc.LongMessage(loc.queue, '...', self.queue.toContent())
                dc.long_messages[qm_id].message = await qm_channel.fetch_message(qm_id)
                print(f"{self.guildid}: done")

        
        # if we were stopped no need to restore more
        if not state == PlayerStates.STOPPED: # TODO: change to current -1 or something similar to restore from stopped
            return True
        
        # try restore vc
        print(f"{self.guildid}: restoring vc")
        channel = next((c for c in guild.voice_channels if c.id == vc_id), None)
        if channel is not None and len(channel.members) > 0:
            # load songs if theres someone in the vc
            self.vc = await channel.connect()
            print(f"{self.guildid}: connected")

            print(f"{self.guildid}: getting songs")
            songs = (await PastQueue(self.guildid).load(1)).get_links()
            print(f"{self.guildid}: done")
            await self.play(None, songs)
            print(f"{self.guildid}: added songs")


            # wait for songs ready
            while self.queue_tracker is None or not self.queue_tracker.done():
                print(f"{self.guildid}: songs lookup...")

                await asyncio.sleep(0.5)

            # play old current
            print(f"{self.guildid}: resuming")
            self.skipSkip = True
            self.vc.stop()
            self.play_from_queue(current, song_time)
            self.state = state

        return True


    def __del__(self):
        print(f"destroying instance for {self.guildid}")


