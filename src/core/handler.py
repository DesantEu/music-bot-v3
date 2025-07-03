import asyncio
from locales import bot_locale as loc
from models.instance import Instance
from network import dcHandler as dc
import os
from storage import db
from discord import ApplicationContext as actx, Bot, Member, VoiceState


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


async def handle_voice(member: Member, before: VoiceState, after: VoiceState):
    if dc.isInVC(member):
        return
    
    inst = instances[member.guild.id]
    if not inst.should_be_connected:
        return
    else:
        print("WE ARE IN HANDLE_VOICE")
        print(f"dc.isInVC(member): {dc.isInVC(member)}")
        print(f"member: {member.name}")
        print(f"b:{before.channel}, a:{after.channel}")
        await inst.on_disconnect()


async def restore_instances(bot: Bot):
    gids = await db.get_guild_ids()

    for gid in gids:
        instances[gid] = Instance(gid, bot)
        await instances[gid].restore()


async def on_exit():
    for i in instances.values():
        await i.save()
    instances.clear()
