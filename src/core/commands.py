from discord.ext.commands import Cog, slash_command, is_owner
from discord.commands import Option
from discord import ApplicationContext as actx
from discord import SlashCommandGroup, Bot

import views
from core import handler
from playback import player
from network import dcHandler as dc
from storage import db
from storage import cacheHandler as cahe
from playback import localPlaylists as lpl
from locales import bot_locale as loc


class User(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot


    @slash_command(
        description="Я ХОЧУ СЛУХАТИ МУЗИКУ",
        options=[
            Option( 
                description="Назва або посилання", 
                name="search", 
                autocomplete=cahe.get_autocomplete
            ),
        ], 
    )
    async def play(self, ctx: actx, song: str):
        inst = handler.getInstance(ctx.guild_id, ctx.bot)

        await player.play(ctx, song, inst)


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


    skip_group = SlashCommandGroup("skip")


    @skip_group.command(
        name="one",
        description="Скіпнути один трек",
    )
    async def skip_one(self, ctx: actx):
        inst = handler.getInstance(ctx.guild_id, ctx.bot)

        if not inst.hasVC():
            await ctx.send_response(dc.reactions.fyou, ephemeral=True)
            return
        if player.skip(inst) == 0:
            await ctx.send_response(dc.reactions.check, ephemeral=True)
        else:
            await ctx.send_response(dc.reactions.cross, ephemeral=True)

    @skip_group.command(
        name="to",
        description="Скіпнути по номеру",
        options=[
            Option( 
                description="Куди скіпаємо?", 
                name="target",
            ),
        ], 
    )
    async def skip_to(self, ctx: actx, target: str):
        inst = handler.getInstance(ctx.guild_id, ctx.bot)

        if not inst.hasVC():
            await ctx.send_response(dc.reactions.fyou, ephemeral=True)
            return
        if player.skip(inst, target) == 0:
            await ctx.send_response(dc.reactions.check, ephemeral=True)
        else:
            await ctx.send_response(dc.reactions.cross, ephemeral=True)


    @slash_command(
        description="Я ХОЧУ ВЗНАТИ ШО ГРАЄ"
    )
    async def queue(self, ctx: actx):
        inst = handler.getInstance(ctx.guild_id, ctx.bot)

        if inst.queue.len() == 0 or not inst.hasVC():
            await ctx.send_response(dc.reactions.fyou, ephemeral=True)
            return

        content = inst.queue.toContent()
        if inst.queue.len() == 0:
            song_title = "..."
        else:
            song_title = f"{loc.now_playing} {inst.current + 1}. {inst.queue[inst.current].title}"
        emb = await dc.send_long(loc.queue, song_title, content, ctx)
        inst.queue_messages.append(emb)


    playlist_group = SlashCommandGroup("playlist")


    @playlist_group.command(
        name="youtube", 
        description="playlist by link"
    )
    async def playlist(self, ctx: actx, link: str):
        await ctx.send_response("шо не работает?", ephemeral=True)


    @playlist_group.command(
        name="local", 
        description="Включити плейліст бота",
        options=[
            Option( 
                description="Назва", 
                name="name", 
                autocomplete=lpl.get_autocomplete
            ),
        ]
    )
    async def playlist_local_play(self, ctx: actx, name: str):
        inst = handler.getInstance(ctx.guild_id, ctx.bot)

        await lpl.play_playlist(ctx, name, inst)


    @playlist_group.command(
        name="check", 
        description="Подивитись шо в плейлісті",
        options=[
            Option( 
                description="Назва", 
                name="name", 
                autocomplete=lpl.get_autocomplete
            ),
        ]
    )
    async def playlist_local_check(self, ctx: actx, name: str):
        await lpl.list_playlists(ctx, name)



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
        # await db.create_cache()
        await ctx.send_response(dc.reactions.fyou, view=views.Queue(), ephemeral=True)

