import discord
from core import parser
from locales import bot_locale as loc
from core.instance import Instance
from network import dcHandler as dc
import os
from playback import player
import os, sys, signal
import atexit
from storage import cacheHandler as cahe

if not os.path.exists('testToken.txt'):
    prefix = '//'
    admin_prefix = '>'
else:
    prefix = '..'
    admin_prefix = ','


admins = ['desantua']

instances:dict[int, Instance] = {}

def getInstance(gid: int, bot) -> Instance:
    if not gid in instances.keys():
        instances[gid] = Instance(gid, prefix, bot)

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
    cahe.save_cache()
    

signal.signal(signal.SIGTERM, handle_sigterm)
signal.signal(signal.SIGINT, handle_sigterm)
atexit.register(on_exit)