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
                autocomplete=ac.local_playlist
            ),
        ]
    )
    async def playlist_local_play(self, ctx: actx, name: str):
        inst = handler.getInstance(ctx.guild_id, ctx.bot)
        playlist = LocalPlaylist(name, ctx.guild_id)

        if not await playlist.load():
            await ctx.send_response(dc.reactions.cross, ephemeral=True)

        if await inst.play(ctx, playlist.song_ids):
            await ctx.send_response(dc.reactions.check, ephemeral=True)
        else:
            await ctx.send_response(dc.reactions.cross, ephemeral=True)


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
        # await db.get_local_playlist_songs(ctx.guild_id, name)
        # await lpl.list_playlists(ctx, name)
        await ctx.send_response(dc.reactions.cross, ephemeral=True)


