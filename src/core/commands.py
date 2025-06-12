from discord.ext.commands import Cog, slash_command, is_owner
from discord.commands import Option
from discord import ApplicationContext as actx
from discord import SlashCommandGroup, Bot

from core import handler
from playback import player
from network import dcHandler as dc
import views
import views.Queue
from storage import db
from storage import cacheHandler as cahe


class User(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot


    @slash_command(
            description="Я ХОЧУ СЛУХАТИ МУЗИКУ",
            options=[
                Option( 
                    description="Назва або посилання", 
                    name="song", 
                    autocomplete=cahe.get_autocomplete
                    ),
                ], 
    )
    async def play(self, ctx: actx, song: str):
        inst = handler.getInstance(ctx.guild_id, ctx.bot)

        await player.play(ctx, song, inst)
        await ctx.send_response(dc.reactions.thumbs_up, view=views.Queue.View(), ephemeral=True)


    @slash_command(
            description="Я НЕ ХОЧУ СЛУХАТИ МУЗИКУ"
    )
    async def stop(self, ctx: actx):
        inst = handler.getInstance(ctx.guild_id, ctx.bot)

        if not inst.hasVC():
            await ctx.respond(dc.reactions.fyou)
            return
        if player.stop(inst) and await dc.leave(inst) == 0:
            await inst.update_queue()
            inst.update_now_playing()
            await ctx.respond(dc.reactions.wave)
        else:
            await ctx.respond(dc.reactions.cross)


    playlist_group = SlashCommandGroup("playlist")


    @playlist_group.command(
            name="youtube", 
            description="playlist by link"
    )
    async def playlist(self, ctx: actx, link: str):
        await ctx.send_response(link, ephemeral=True)


    @playlist_group.command(
            name="local", 
            description="playlist by name"
    )
    async def playlist_local(self, ctx: actx, name):
        await ctx.send_response(name, ephemeral=True)

    






class Admin(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        
    cache = SlashCommandGroup(
        "cache", 
        "BACKEND BS BE CAREFUL",
        checks=[is_owner()],
    )

    @cache.command(name="drop")
    async def cache_drop(self, ctx: actx):
        await db.drop_cache()
        await ctx.send_response(dc.reactions.check, ephemeral=True)

    @cache.command(name="create")
    async def cache_create(self, ctx: actx):
        await db.create_cache()
        await ctx.send_response(dc.reactions.check, ephemeral=True)

    @cache.command(name="select")
    async def cache_select(self, ctx: actx):
        await db.select_cache()
        await ctx.send_response(dc.reactions.check, ephemeral=True)

    @cache.command(name="add")
    async def cache_add(self, ctx: actx):
        await db.add_cache("fsdafa", "fortnite balls", "123", ["asasdsad", "342342"])
        await ctx.send_response(dc.reactions.check, ephemeral=True)

    @slash_command()
    async def test(self, ctx: actx):
        await db.create_cache()
        await ctx.send_response(dc.reactions.fyou, view=views.Queue.View(), ephemeral=True)

