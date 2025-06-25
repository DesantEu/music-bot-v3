import asyncio
import os, json
from asyncio import sleep

from discord.ext.commands import Cog, slash_command, is_owner
from discord.commands import Option
from discord import ApplicationContext as actx
from discord import SlashCommandGroup, Bot

from core import handler
from models.autocomplete import Autocomplete as ac
from network import dcHandler as dc

class Player(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot


    @slash_command(
        description="Я ХОЧУ СЛУХАТИ МУЗИКУ",
        options=[
            Option( 
                description="Назва або посилання", 
                name="search", 
                autocomplete=ac.song
            ),
        ], 
    )
    async def play(self, ctx: actx, song: str):
        inst = handler.getInstance(ctx)

        await dc.check_cross(ctx, await inst.play(ctx, song))


    @slash_command(
        description="Я НЕ ХОЧУ СЛУХАТИ МУЗИКУ"
    )
    async def stop(self, ctx: actx):
        inst = handler.getInstance(ctx)
        res = await inst.stop() and await inst.leave()
        
        await dc.check_cross(ctx, res)


    @slash_command(
        name="skip",
        description="Скіпнути один трек",
    )
    async def skip_one(self, ctx: actx):
        inst = handler.getInstance(ctx)

        await dc.check_cross(ctx, inst.skip())


    @slash_command(
        name="goto",
        description="Скіпнути по номеру",
        options=[
            Option( 
                description="Куди скіпаємо?", 
                name="target",
            ),
        ], 
    )
    async def skip_to(self, ctx: actx, target: str):
        inst = handler.getInstance(ctx)
        
        await dc.check_cross(ctx, inst.skip(target))