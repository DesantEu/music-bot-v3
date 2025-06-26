import asyncio

from discord.ext.commands import Cog
from discord.commands import Option
from discord import ApplicationContext as actx
from discord import SlashCommandGroup, Bot

from core import handler
from models.local_playlist import LocalPlaylist
from models.autocomplete import Autocomplete as ac
from network import dcHandler as dc
from locales import bot_locale as loc
from models.enums import reactions
from models.playlist import Playlist as YtPlaylist

class Playlist(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    playlist_group = SlashCommandGroup("playlist")


    @playlist_group.command(
        name="play", 
        description="Включити плейліст бота",
        options=[
            Option( 
                description="Назва", 
                name="name", 
                autocomplete=ac.local_playlist
            ),
        ]
    )
    async def playlist_local_play(self, ctx: actx, name: str):
        inst = handler.getInstance(ctx)
        links = (await LocalPlaylist(name, ctx.guild_id).load()).get_links()

        await dc.check_cross(ctx, await inst.play(ctx, links))


    @playlist_group.command(
        name="save",
        description="Зберегти чергу як плейліст",
        options=[
            Option(
                description="Назва",
                name="name"
            )
        ]
    )
    async def playlist_local_save(self, ctx: actx, name: str):
        inst = handler.getInstance(ctx)

        # song_ids = [s.id for s in inst.queue]
        res = await LocalPlaylist(name, ctx.guild_id, inst.queue.q).save()

        await dc.check_cross(ctx, res)


    @playlist_group.command(
        name="check", 
        description="Подивитись шо в плейлісті",
        options=[
            Option( 
                description="Назва", 
                name="name", 
                autocomplete=ac.local_playlist
            ),
        ]
    )
    async def playlist_local_check(self, ctx: actx, name: str):
        inst = handler.getInstance(ctx)
        content = (await LocalPlaylist(name, ctx.guild_id).load()).get_content()

        if content == []:
            await ctx.send_response(dc.reactions.cross, ephemeral=True)
            return


        await dc.send_long(name, loc.filler, content, ctx, ephemeral=True)


    @playlist_group.command(
        name="youtube", 
        description="playlist by link",
        options=[
            Option(
                description="Назва або лінк",
                name="prompt",
                autocomplete=ac.playlist
            )
        ]
    )
    async def playlist_youtube(self, ctx: actx, link: str):
        inst = handler.getInstance(ctx)
        await ctx.send_response(reactions.search, ephemeral=True)

        try:
            pl = await YtPlaylist.search(link, inst.queue)
            await inst.play(ctx, pl.get_links())

            await ctx.interaction.delete_original_response()

        except Exception as e:
            print(f"Error while searching playlist: {e}")
            await ctx.interaction.edit_original_response(
                content=reactions.cross,
            )
            await asyncio.sleep(1)
            await ctx.interaction.delete_original_response()


