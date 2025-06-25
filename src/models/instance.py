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
        """0 by default, means no queue message"""
        self.queue_tracker = None

        self._update_content_task:  asyncio.Task | None = None
        self._update_title_task:    asyncio.Task | None = None
        self._save_task:            asyncio.Task | None = None
        self._restore_task:         asyncio.Task | None = None

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
        if ctx is None:
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
        print(f"updating queue embed for {self.guildid}")
        # cancel old task 
        if self._update_content_task is not None and not self._update_content_task.done():
            self._update_content_task.cancel()
            print(f"canceled old update task for {self.guildid}")

        self._update_content_task = asyncio.create_task(
            self._update_queue_embed_now()
        )
        

    async def _update_queue_embed_now(self):
        print(f"debouncing update for {self.guildid}")
        await asyncio.sleep(0.3)  # debounce time

        content = self.queue.toContent()
        old = dc.long_messages[self.queue_message].content

        if content == old:
            return
        print(f"content changed for {self.guildid}, updating")
        
        await dc.edit_long_content(self.queue_message, content)


    def update_now_playing(self):
        # if we have a task running, cancel it
        if self._update_title_task is not None and not self._update_title_task.done():
            self._update_title_task.cancel()
            print(f"canceled old title update task for {self.guildid}")

        self._update_title_task = self.bot.loop.create_task(
            self._update_title_now()
        )


    async def _update_title_now(self):
        print(f"debouncing title update for {self.guildid}")
        await asyncio.sleep(0.3)

        song_title = self.__get_now_playing()
        old_title = dc.long_messages[self.queue_message].smaller_title

        if song_title == old_title:
            return
        print(f"title changed for {self.guildid}, updating")

        await dc.edit_long_smaller_title(self.queue_message, song_title)
        

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


    async def join(self, ctx: actx | discord.VoiceChannel) -> bool:
        # grab channel
        channel: discord.VoiceChannel
        if type(ctx) is actx:
            channel = ctx.user.voice.channel
        elif type(ctx) is discord.VoiceChannel:
            channel = ctx
        else:
            print(f"join called with {type(ctx)}")
            return False


        try:
            # connect if not yet connected
            if not self.has_vc():
                self.vc = await channel.connect()
                return True
            # move to other channel maybe
            if not self.vc.channel == channel:
                await self.vc.move_to(channel)
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
        await self.stop()
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


    async def restore(self, force_join = False) -> bool:
        """ Restores the player state from the database.
        If force_join is True, it will restore the player even if it was stopped.
        Returns True if the player was restored successfully, False otherwise.
        """
        # if we have a task running, cancel it
        if self._restore_task is not None and not self._restore_task.done():
            self._restore_task.cancel()
            print(f"canceled old restore task for {self.guildid}")

        self._restore_task = asyncio.create_task(
            self._restore_now(force_join)
        )
        
        return True
    


    async def _restore_now(self, force_join = False) -> bool:
        # debounce
        await asyncio.sleep(0.3)
        
        print(f"restoring session for {self.guildid}")

        # get state
        res = await db.get_state(self.guildid)
        if res is None:
            return False
        print(f"{self.guildid}: got state")
        
        # unpack
        state, current, song_time, vc_id, qm_id, qc_id = res
        # guilds that have used commands but never saved can have nulls all over this
        # we dont want that
        if not all(i is not None for i in [state, current, song_time, vc_id, qm_id, qc_id]):
            print(f"{self.guildid}: incomplete state, restoring stopped")
            return True
        
        # get this instances guild
        guild = self.bot.get_guild(self.guildid)
        if guild is None:
            return False
        print(f"{self.guildid}: got guild")
        
        # try restore queue message
        try:
            if qc_id > 0:
                qm_channel = guild.get_channel(qc_id) # need channel
                if type(qm_channel) is discord.TextChannel:
                    # create placeholder long message
                    print(f"{self.guildid}: creating queue message")
                    self.queue_message = qm_id
                    dc.long_messages[qm_id] = dc.LongMessage(loc.queue, '...', self.queue.toContent())
                    dc.long_messages[qm_id].message = await qm_channel.fetch_message(qm_id)
                    print(f"{self.guildid}: done")
        except Exception as e:
            print(f"{self.guildid}: queue message likely deleted")
            self.queue_message = 0
            return False

        
        # if we were stopped no need to restore more
        if state == PlayerStates.STOPPED and not force_join:
            return True
        
        # try restore vc
        print(f"{self.guildid}: restoring vc")
        channel = next((c for c in guild.voice_channels if c.id == vc_id), None)
        if channel is not None and len(channel.members) > 0:
            # load songs if theres someone in the vc
            await self.join(channel)
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


