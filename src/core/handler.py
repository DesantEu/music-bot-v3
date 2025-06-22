import asyncio
from locales import bot_locale as loc
from models.instance import Instance
from network import dcHandler as dc
import os
from storage import db
from discord import ApplicationContext as actx, Bot


admins = ['desantua']

instances:dict[int, Instance] = {}

def getInstance(ctx: actx) -> Instance:
    gid = ctx.guild_id
    bot = ctx.bot

    if not gid in instances.keys():
        instances[gid] = Instance(gid, bot)
        if ctx.guild is not None:
            asyncio.create_task(db.track_guild(ctx.guild_id, ctx.guild.name))


    return instances[gid]


async def handle_voice(member, before, after):
    if not dc.isInVC(member):
        await instances[member.guild.id].on_disconnect()


async def restore_instances(bot: Bot):
    gids = await db.get_guild_ids()

    for gid in gids:
        instances[gid] = Instance(gid, bot)
        await instances[gid].restore()


async def on_exit():
    for i in instances.values():
        await i.save()
    instances.clear()
