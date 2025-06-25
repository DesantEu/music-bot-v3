import asyncio
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
        inst = handler.getInstance(ctx)

        if not await inst.send_queue(ctx) == -1:
            await ctx.send_response(dc.reactions.check, ephemeral=True)


    past_group = SlashCommandGroup("past")


    @past_group.command(
        name="check",
        description="Показує попередні черги"
    )
    async def past_list(self, ctx: actx):
        inst = handler.getInstance(ctx)

        content = await PastQueue(ctx.guild_id).get_content()
        await dc.send_long(loc.rmlist_title, loc.qq_smaller_title, content, ctx, ephemeral=True)


    @past_group.command(
        name="play",
        description="ХОЧУ СЛУХАТИ ЯК РАНІШЕ",
        options=[
            Option(
                scot.integer,
                description="Цифру брати з /past check",
                name="number"
            )
        ]
    )
    async def past_play(self, ctx: actx, index: int):
        inst = handler.getInstance(ctx)
        pq = (await PastQueue(ctx.guild_id).load(index)).get_links()

        await dc.check_cross(ctx, await inst.play(ctx, pq))


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
        inst = handler.getInstance(ctx)

        await dc.check_cross(ctx, await inst.remove(query, ctx))
        await inst.update_queue_embed()


    @slash_command(
        description="Я ХОЧУ ОЧИСТИТИ МУЗИКУ"
    )
    async def clear(self, ctx: actx):
        inst = handler.getInstance(ctx)

        if not inst.has_vc() or inst.queue.len() == 0:
            await ctx.send_response(dc.reactions.fyou, ephemeral=True)
            await asyncio.sleep(5)
            await ctx.interaction.delete_original_response()
            return

        if await inst.stop(f"{ctx.author.display_name} очистив чергу") and await inst.leave():
            inst.update_now_playing()
            await inst.update_queue_embed()
            
            await ctx.send_response(dc.reactions.check, ephemeral=True)
            await asyncio.sleep(1)
            await ctx.interaction.delete_original_response()

        else:
            await ctx.send_response(dc.reactions.cross, ephemeral=True)
            await asyncio.sleep(5)
            await ctx.interaction.delete_original_response()


    @slash_command(
        description="ХТОСЬ ВИКЛЮЧИВ БОТА ПОВЕРНІТЬ ЯК БУЛО",
    )
    async def restore(self, ctx: actx):
        inst = handler.getInstance(ctx)

        await dc.check_cross(ctx, await inst.restore(force_join=True))
