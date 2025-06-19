import discord
from core import parser
from locales import bot_locale as loc
from models.instance import Instance
from network import dcHandler as dc
import os
import os, sys, signal
import atexit
from discord import Bot


admins = ['desantua']

instances:dict[int, Instance] = {}

def getInstance(gid: int, bot: Bot) -> Instance:
    if not gid in instances.keys():
        instances[gid] = Instance(gid, bot)

    return instances[gid]


async def handle_voice(member, before, after):
    if not dc.isInVC(member):
        await instances[member.guild.id].on_disconnect()


def handle_sigterm(signum, frame):
    # on_exit()
    sys.exit(0)


def on_exit():
    pass
    instances.clear()
    

signal.signal(signal.SIGTERM, handle_sigterm)
signal.signal(signal.SIGINT, handle_sigterm)
atexit.register(on_exit)