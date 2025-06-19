import os, json
from asyncio import sleep

from discord.ext.commands import Cog, slash_command, is_owner
from discord.commands import Option
from discord import ApplicationContext as actx
from discord import SlashCommandGroup, SlashCommandOptionType as scot, Bot

import views
from core import handler
from models import local_playlist as lpl
from models.past_queue import PastQueue
from models.autocomplete import Autocomplete as ac
from network import dcHandler as dc
from locales import bot_locale as loc
from storage import db

class Queue(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot



    @slash_command(
        description="Я ХОЧУ ВЗНАТИ ШО ГРАЄ"
    )
    async def queue(self, ctx: actx):
        inst = handler.getInstance(ctx.guild_id, ctx.bot)

        if not await inst.send_queue(ctx) == -1:
            await ctx.send_response(dc.reactions.check, ephemeral=True)


    past_group = SlashCommandGroup("past")

    @past_group.command(
        name="list",
        description="Показує попередні черги"
    )
    async def past_list(self, ctx: actx):
        inst = handler.getInstance(ctx.guild_id, ctx.bot)
        content = await PastQueue.get_as_content(ctx.guild_id)

        if content == []:
            await ctx.send_response(dc.reactions.fyou, ephemeral=True)
            return
        
        await dc.send_long(loc.rmlist_title, loc.qq_smaller_title, content, ctx, ephemeral=True)


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
        await ctx.send_response(dc.reactions.fyou, ephemeral=True)

        # if index < 1 or index > len(inst.past_queues):
        #     await ctx.send_response(dc.reactions.fyou, ephemeral=True)
        #     return

        # await past.play_past_queue(index-1, inst, ctx)


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

        if inst.queue.len() == 0 or not inst.has_vc():
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
                # past.add_rmlist(inst, res) # TODO: rmlist
                # stop if queue is empty
                if inst.queue.len() == 0:
                    inst.stop()
                success = True

        inst.current -= current_reduce

        await inst.update_queue_embed()
        if skip_later:
            inst.current -= 1
            if not inst.skip():
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

        if not inst.has_vc() or inst.queue.len() == 0:
            await ctx.send_response(dc.reactions.fyou, ephemeral=True)
            return

        if inst.stop():
            inst.update_now_playing()
            await inst.update_queue_embed()
            await ctx.send_response(dc.reactions.check, ephemeral=True)

        else:
            await ctx.send_response(dc.reactions.cross, ephemeral=True)
