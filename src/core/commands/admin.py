from discord.ext.commands import Cog, slash_command, is_owner
from discord.commands import Option
from discord import ApplicationContext as actx
from discord import SlashCommandGroup, SlashCommandOptionType as scot, Bot

import views
from network import dcHandler as dc
from locales import bot_locale as loc
from storage import db


class Admin(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        
    cache = SlashCommandGroup(
        "cache", 
        "BACKEND BS BE CAREFUL",
        checks=[is_owner()],
    )

    # @cache.command(name="transfer")
    # async def cache_transfer(self, ctx: actx):
    #     await db.drop_all()
    #     await sleep(1)
    #     await db.ensure_tables()
    #     await sleep(1)
    #     await db.track_guild(ctx.guild_id, ctx.guild.name)
        
    #     for song in cahe.cache:
    #         s = cahe.cache[song]
    #         print(f"adding song: {s.title}")
    #         # await db.add_cache(s.link, s.title, s.searches)
    #         await db.add_song(s.link, s.title, s.searches)

    #     for playlist in cahe.playlist_cache:
    #         p = cahe.playlist_cache[playlist]
    #         print(f"adding playlist: {p.title}")
    #         await db.add_playlist(p.link, p.title, p.searches)

    #     path = 'playlists'
    #     files = [f[:-4] for f in os.listdir(path) if f.endswith('.lpl')]
    #     for name in files:
    #         filepath = f'playlists/{name}.lpl'
    #         with open(filepath, 'r', encoding='utf-8') as file:
    #             print(f"PLAYLIST: {name}")
    #             data: dict = json.loads(file.read())
    #             songs = [data[s] for s in data.keys()]
    #             real_songs = []
    #             for i in range(len(songs)):
    #                 if songs[i].startswith("ytsearch1:"):
    #                     vid, song = await db.search_song(songs[i][songs[i].index(":")+1:])
    #                     if not vid == '':
    #                         real_songs.append(vid)
    #                 elif "?v=" in songs[i]:
    #                     real_songs.append(songs[i][songs[i].index("?v=")+3:])
    #             print(real_songs)
    #             await db.add_local_playlist(ctx.guild_id, name, real_songs)

    #     await ctx.send_response(dc.reactions.check, view=views.Queue(), ephemeral=True)


    @cache.command(name="search")
    async def cache_search(self, ctx: actx, query: str):
        await db.search_song(query)
        await ctx.send_response(dc.reactions.check, ephemeral=True)

    @cache.command(name="drop")
    async def cache_drop_all(self, ctx: actx):
        await db.drop_all()
        await ctx.send_response(dc.reactions.check, ephemeral=True)

    @cache.command(name="create")
    async def cache_create_tables(self, ctx: actx):
        await db.ensure_tables()
        await ctx.send_response(dc.reactions.check, ephemeral=True)


    @slash_command()
    async def test(self, ctx: actx):
        # await db.create_cache()
        await ctx.send_response(dc.reactions.fyou, view=views.Queue(), ephemeral=True)

