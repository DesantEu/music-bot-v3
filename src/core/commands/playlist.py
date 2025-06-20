import os, json
from asyncio import sleep

from discord.ext.commands import Cog, slash_command, is_owner
from discord.commands import Option
from discord import ApplicationContext as actx
from discord import SlashCommandGroup, SlashCommandOptionType as scot, Bot

import views
from core import handler
from models.local_playlist import LocalPlaylist
from models.autocomplete import Autocomplete as ac
from network import dcHandler as dc
from locales import bot_locale as loc
from storage import db

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
        inst = handler.getInstance(ctx.guild_id, ctx.bot)
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
        inst = handler.getInstance(ctx.guild_id, ctx.bot)

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
        inst = handler.getInstance(ctx.guild_id, ctx.bot)
        content = (await LocalPlaylist(name, ctx.guild_id).load()).get_content()

        if content == []:
            await ctx.send_response(dc.reactions.cross, ephemeral=True)
            return


        await dc.send_long(name, loc.filler, content, ctx, ephemeral=True)


    @playlist_group.command(
        name="youtube", 
        description="playlist by link"
    )
    async def playlist_youtube(self, ctx: actx, link: str):
        await ctx.send_response("шо не работает?", ephemeral=True)


