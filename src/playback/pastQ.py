import discord
from locales import bot_locale as loc
from network import dcHandler as dc
from playback import playlists
from playback import player

def add_rmlist(inst, song_name: str):
    inst.rmlist.append(song_name)
    if len(inst.rmlist) > 50:
        inst.rmlist.pop(0)

async def send_rmlist(inst, message: discord.Message):
    if len(inst.rmlist) == 0:
        await message.add_reaction(dc.reactions.fyou)
        return

    content = []

    for i in inst.rmlist:
        content.append(['>', i])
    
    await dc.send_long(loc.rmlist_title, loc.rmlist_smaller_title, content, message.channel)

def add_past_queue(inst):
    if inst.queue.len() == 0:
        return

    inst.past_queues.insert(0, inst.queue.copy())
    if len(inst.past_queues) > 10:
        _ = inst.past_queues.pop(-1)

async def send_past_queues(inst, message: discord.Message):
    if len(inst.past_queues) == 0:
        await message.add_reaction(dc.reactions.fyou)
        return

    content = []
    for i in range(len(inst.past_queues)):
        content.append([f'{i+1}. ', ' '])
        for j in inst.past_queues[i]:
            content.append(['> ', j.title])

    await dc.send_long(loc.rmlist_title, loc.qq_smaller_title, content, message.channel)


async def play_past_queue(index: int, inst, message: discord.Message):
    # send notif
    content = [[f'{inst.queue.len()}. ', i.title] for i in inst.past_queues[index]]
    await dc.send_long(loc.rmlist_title, loc.qq_smaller_title, content, message.channel)

    # add songs from past queue to current queue
    for i in inst.past_queues[index]:
        inst.queue.append(i.link, i.title)

    await inst.update_queue()

    # if nothing is playing we should start playing i guess
    if not dc.isInVC(message.author):
        await dc.send(loc.left_vc, message.channel)
        return -1
    else:
        await dc.join(message, inst)
        if not inst.isPlaying:
            player.play_from_queue(0, inst) # TODO: remove
