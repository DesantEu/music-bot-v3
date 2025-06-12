import discord
from discord import ApplicationContext as actx
from network import ytHandler as yt
from network import dcHandler as dc
from locales import bot_locale as loc
# from playback import playlists
import re
from playback import pastQ as past
from storage import cacheHandler as cahe

async def play(ctx: actx, prompt:str, inst):
    # handle empty prompts
    if prompt == '' and not inst.isPaused:
        await ctx.send_response(dc.reactions.fyou, ephemeral=True)
        return

    # check if the user is in a vc
    if not dc.isInVC(ctx.author):
        await ctx.send_response(loc.no_vc, ephemeral=True)
        return -1


    isSuccessful = -1

    # handle links
    if prompt.startswith('https://'):
        # handle playlists
        if 'list=' in prompt:
            isSuccessful = await cahe.find_link_play(ctx, yt.remove_playlist_from_link(prompt), inst)

        # handle a single song
        else:
            isSuccessful = await cahe.find_link_play(ctx, prompt, inst)
    # handle text search
    else:
        isSuccessful = await cahe.find_prompt_play(ctx, prompt, inst)

    if not isSuccessful == 0:
        return -1

    # check vc again just to be sure
    if not dc.isInVC(ctx.author):
        await ctx.send_response(loc.left_vc, ephemeral=True)
        return -1
    else:
        await dc.join(ctx, inst)
        if not inst.isPlaying:
            play_from_queue(0, inst) # TODO: remove
    
            
def stop(inst) -> bool:

    # stop and leave vc
    if inst.hasVC():
    # drop play.after
        inst.skipSkip = True
        inst.vc.stop()
    # else:
    #     return False

    inst.isPaused = False
    inst.isPlaying = False
    inst.isStopped = True
    past.add_past_queue(inst)
    inst.queue.clear()
    return True


def resume(inst) -> bool:
    inst.isPlaying = True
    inst.isStopped = False
    inst.isPaused = False
    return True

def pause(inst) -> bool:
    inst.isPlaying = False
    inst.isStopped = False
    inst.isPaused = True
    return True

def skip(inst, num='', afterSong=False) -> int:
    if not inst.hasVC():
        return -1

    if inst.queue.len() == 0:
        return -1

    # handle numbers:
    if not num == '':
        try:
            num = int(num)
        except:
            return -1

        if num < 0 or num > inst.queue.len():
            return -1
        
        if num == 0:
            next = 0
        else:
            next = num - 1
    # skip no number
    else:
        next = inst.current + 1
        # roll over forward
        if next >= inst.queue.len():
            next = 0

    # drop play.after to avoid recursive skipping
    if inst.vc.is_playing():
        if not afterSong:
            inst.skipSkip = True
        inst.vc.stop()

    play_from_queue(next, inst)
    return 0
    

def play_from_queue(index, inst):
    title = inst.queue[index].link
    file = 'songs/' + re.sub(r'[\|/,:&$#"]', '', yt.get_id_from_link(title)) + '.mp3'

    inst.vc.play(discord.FFmpegPCMAudio(file), after=inst.after_song)
    inst.current = index
    inst.update_now_playing()
    resume(inst)


async def handle_reaction(reaction, inst) -> int:
    # instaplay
    if reaction.emoji == dc.reactions.play:
        # check if we have the message in question
        is_insta = False
        index = ''
        for i in inst.queue:
            if i.instaplay_message == reaction.message.id:
                is_insta = True
                index = inst.queue.index(i)
                # exit function with error if the index is wrong
                if index == -1 or index is None:
                    return 1
                break

        if is_insta and inst.queue[index].can_instaplay:
            inst.queue[index].can_instaplay = False
            return skip(inst, str(int(index) + 1))

    return -1


