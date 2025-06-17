from discord.ext.commands import Cog, slash_command, is_owner
from discord.commands import Option
from discord import ApplicationContext as actx
from discord import SlashCommandGroup, SlashCommandOptionType as scot, Bot

import views
from core import handler
from playback import player
from network import dcHandler as dc
from storage import db
from storage import cacheHandler as cahe
from playback import localPlaylists as lpl
from locales import bot_locale as loc
from playback import pastQ as past
import os, json
from asyncio import sleep


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


    past_group = SlashCommandGroup("past")


    @past_group.command(
        name="list",
        description="Показує попередні черги"
    )
    async def past_list(self, ctx: actx):
        inst = handler.getInstance(ctx.guild_id, ctx.bot)

        if len(inst.past_queues) == 0:
            await ctx.send_response(dc.reactions.fyou, ephemeral=True)
            return

        await past.send_past_queues(inst, ctx)


    @past_group.command(
        name="play",
        description="ХОЧУ СЛУХАТИ ЯК РАНІШЕ",
        options=[
            Option(
                scot.integer,
                description="Цифру брати з /past list",
                name="number"
            )
        ]
    )
    async def past_play(self, ctx: actx, index: int):
        inst = handler.getInstance(ctx.guild_id, ctx.bot)

        if index < 1 or index > len(inst.past_queues):
            await ctx.send_response(dc.reactions.fyou, ephemeral=True)
            return

        await past.play_past_queue(index-1, inst, ctx)


    @slash_command(
        description="Я НЕ ХОЧУ СЛУХАТИ КОНКРЕТНУ МУЗИКУ",
        options=[
            Option(
                description="Наприклад: 1 3 5-7 10",
                name="songs"
            )
        ]
    )
    async def remove(self, ctx: actx, query: str):
        inst = handler.getInstance(ctx.guild_id, ctx.bot)

        if inst.queue.len() == 0 or not inst.hasVC():
            await ctx.send_response(dc.reactions.fyou, ephemeral=True)
            return

        removes = query.split(' ')
        success = False
        warns = 0
        max = inst.queue.len()

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
                    warns += 1
                    continue
                # only pick (1-25)-123
                elif len(splits) > 2:
                    warns += 1
                try:
                    start = int(splits[0])
                    end = int(splits[1])
                    if end > max:
                        end = max
                        warns += 1
                # if letters are thrown in the sequence
                except:
                    warns += 1
                    continue

                # yea this would happen somehow
                if end < start:
                    warns += 1
                    continue

                for ind in range(start, end+1):
                    if ind > max:
                        warns += 1
                        continue

                    if not ind in indeces:
                        indeces.append(ind)

            # handle single numbers
            else:
                # parse int of course
                try:
                    ind = int(i)
                    if ind > max:
                        warns += 1
                        continue

                    if not i in indeces:
                        indeces.append(ind)
                # letters detected here
                except:
                    warns += 1
                    continue

        print('warns: ' + str(warns))

        # my honest reaction:
        if warns >= 3:
            print('reaction triggered')
            await ctx.send_response("Вумний?", ephemeral=True)


        # ensure they are unique
        temp = []
        for i in indeces:
            if not i in temp:
                temp.append(i)
        indeces = temp

        # reverse and delete from end cuz indeces change and shit
        indeces = sorted(indeces, reverse=True)
        current_reduce = 0
        skip_later = inst.current in indeces

        for i in indeces:
            if i <= inst.current:
                current_reduce += 1

            res = inst.queue.pop(str(i))
            if not res == '':
                # save to rmlist
                past.add_rmlist(inst, res)
                # stop if queue is empty
                if inst.queue.len() == 0:
                    player.stop(inst)
                success = True

        inst.current -= current_reduce

        await inst.update_queue()
        if skip_later:
            inst.current -= 1
            if not player.skip(inst) == 0:
                warns += 1
        else:
            inst.update_now_playing()


        if success:
            if warns >= 3:
                await ctx.send_followup("Прибрав, але не без проблем", ephemeral=True)
            elif warns > 0:
                await ctx.send_response("Прибрав, але не без проблем", ephemeral=True)

            else:
                await ctx.send_response("Прибрав", ephemeral=True)

        else:
            await ctx.send_response(dc.reactions.cross, ephemeral=True)


    @slash_command(
        description="Я ХОЧУ ОЧИСТИТИ МУЗИКУ"
    )
    async def clear(self, ctx: actx):
        inst = handler.getInstance(ctx.guild_id, ctx.bot)

        if not inst.hasVC() or inst.queue.len() == 0:
            await ctx.send_response(dc.reactions.fyou, ephemeral=True)
            return

        if player.stop(inst):
            inst.update_now_playing()
            await inst.update_queue()
            await ctx.send_response(dc.reactions.check, ephemeral=True)

        else:
            await ctx.send_response(dc.reactions.cross, ephemeral=True)



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
        await db.get_local_playlist_songs(ctx.guild_id, name)
        await lpl.list_playlists(ctx, name)



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
        await db.drop_all()
        await sleep(1)
        await db.ensure_tables()
        await sleep(1)
        await db.track_guild(ctx.guild_id, ctx.guild.name)
        
        for song in cahe.cache:
            s = cahe.cache[song]
            print(f"adding song: {s.title}")
            # await db.add_cache(s.link, s.title, s.searches)
            await db.add_song(s.link, s.title, s.searches)

        for playlist in cahe.playlist_cache:
            p = cahe.playlist_cache[playlist]
            print(f"adding playlist: {p.title}")
            await db.add_playlist(p.link, p.title, p.searches)

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
                        real_songs.append(songs[i][songs[i].index("?v=")+3:])
                print(real_songs)
                await db.add_local_playlist(ctx.guild_id, name, real_songs)

        await ctx.send_response(dc.reactions.check, view=views.Queue(), ephemeral=True)


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

