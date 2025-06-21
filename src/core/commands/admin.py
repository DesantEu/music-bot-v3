import asyncio
from discord.ext.commands import Cog, slash_command, is_owner
from discord.commands import Option
from discord import ApplicationContext as actx
from discord import SlashCommandGroup, SlashCommandOptionType as scot, Bot

from models.past_queue import PastQueue
import views, os, json
from network import dcHandler as dc, ytHandler as yt
from locales import bot_locale as loc
from storage import db
from core import handler


class Admin(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        
    cache = SlashCommandGroup(
        "cache", 
        "BACKEND BS BE CAREFUL",
        checks=[is_owner()],
    )

    @cache.command(name="transfer")
    async def cache_transfer(self, ctx: actx):
        await db.lpl_drop()
        await asyncio.sleep(1)
        await db.lpl_create()
        await db.track_guild(ctx.guild_id, ctx.guild.name)


        path = 'playlists'
        files = [f[:-4] for f in os.listdir(path) if f.endswith('.lpl')]
        for name in files:
            filepath = f'playlists/{name}.lpl'
            with open(filepath, 'r', encoding='utf-8') as file:
                print(f"PLAYLIST: {name}")
                data: dict = json.loads(file.read())
                songs = [data[s] for s in data.keys()]
                real_songs = []
                for i in range(len(songs)):
                    if songs[i].startswith("ytsearch1:"):
                        vid, song = await db.search_song(songs[i][songs[i].index(":")+1:])
                        if not vid == '':
                            real_songs.append(vid)
                    elif "?v=" in songs[i]:
                        real_songs.append(yt.get_id_from_link(songs[i]))
                print(real_songs)

                await db.add_local_playlist(ctx.guild_id, name, real_songs)

        await ctx.send_response(dc.reactions.check, view=views.Queue(), ephemeral=True)


    @cache.command(name="drop_lpl")
    async def drop_lpl(self, ctx: actx):
        await db.lpl_drop()
        await dc.check_cross(ctx, True)


    @slash_command()
    async def test(self, ctx: actx):
        # await db.create_cache()
        await ctx.send_response(dc.reactions.fyou, view=views.Queue(), ephemeral=True)


    past = SlashCommandGroup("admin_past", "admin bs", checks=[is_owner()])

    @past.command(name="save", description="force save current queue")
    async def past_save(self, ctx:actx):
        inst = handler.getInstance(ctx)

        pq = PastQueue(ctx.guild_id, inst.queue.q)

        await dc.check_cross(ctx, await pq.save())

