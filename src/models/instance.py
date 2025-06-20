import discord
import asyncio
from models.player import Player
from models.song import SongStatus
from network import dcHandler as dc
from locales import bot_locale as loc
from discord import ApplicationContext as actx


class Instance(Player):
    def __init__(self, gid:int, bot: discord.Client):
        super().__init__()
        self.guildid: int = gid
        self.queue_message: int = -1
        self.queue_tracker = None

        self.bot = bot
        # self.vc: discord.VoiceClient
        # TODO: load session

        print(f"created instance {self.guildid}")


    async def play(self, ctx: actx, prompt: str | list[str]) -> bool:
        if not dc.isInVC(ctx.user):
            return False
        await self.join(ctx)

        play_success = await super().play(ctx, prompt)
        if not play_success:
            return False
        # send queue
        if self.queue_message == -1:
            await self.send_queue(ctx)
        # track song status
        if self.queue_tracker is None or self.queue_tracker.done():
            self.queue_tracker = asyncio.create_task(self.track_queue())
        return play_success



    async def send_queue(self, ctx: actx) -> int:
        if self.queue.len() == 0:
            return -1

        song_title = self.__get_now_playing()
        content = self.queue.toContent()
        emb = await dc.send_long(loc.queue, song_title, content, ctx, respond=False)
        self.queue_message = emb

        return emb
    

    async def track_queue(self):
        # wait for ready
        while not all(song.status == SongStatus.READY for song in self.queue):
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

    



    def __del__(self):
        print(f"destroying instance for {self.guildid}")
        self.stop()
        asyncio.run(self.leave())
        # TODO: save session


