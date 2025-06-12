from network import dcHandler as dc
from locales import bot_locale as loc
from playback import player
from storage import cacheHandler as cahe
from discord import ApplicationContext as actx

import os

from network import ytHandler as yt

async def play_bulk(prompts: list[str], inst, ctx: actx, title:str=loc.rmlist_title, sub_title=loc.bulk_smaller_title) -> int:
    content = [['> ', i] for i in prompts]
    song_available = False
    tried_connecting = False

    # notify the server
    emb = await dc.send_long(title, sub_title, content, ctx)

    # add songs to queue
    for ind in range(len(prompts)):
        pr = prompts[ind]

        # handle words
        if not 'https://' in pr:
            # check if the song will be loaded quickly
            if not (pr.lower() in cahe.search_cache and os.path.exists(f"songs/{cahe.search_cache[pr.lower()].link}.mp3")):
                content[ind] = ["⌬ ", pr]
                await dc.edit_long_content(emb, content)

            if await cahe.find_prompt_play(ctx, pr, inst, silent=True, skipQueueUpdate=True) == 0:
                content[ind] = [f'{inst.queue.len()}.  ', inst.queue[inst.queue.len()-1].title]

                song_available = True

        # handle links
        else:
            # check if the song will be loaded quickly
            id = yt.get_id_from_link(pr)
            if not (id in cahe.cache and os.path.exists(f"songs/{id}.mp3")):
                content[ind] = ["⌬ ", pr]
                await dc.edit_long_content(emb, content)

            if await cahe.find_link_play(ctx, pr, inst, silent=True, skipQueueUpdate=True) == 0:
                content[ind] = [f'{inst.queue.len()}.  ', inst.queue[inst.queue.len()-1].title]

                song_available = True


        # if nothing is playing we should start playing i guess
        if song_available and not tried_connecting:
            tried_connecting = True
            # check vc again just to be sure
            if not dc.isInVC(ctx.user):
                await ctx.send_response(loc.left_vc, ephemeral=True)
                return -1
            else:
                await dc.join(ctx, inst)
                if not inst.isPlaying:
                    player.play_from_queue(0, inst) # TODO: remove

    # check vc again just for fun
    if not dc.isInVC(ctx.user):
        await ctx.send_response(loc.left_vc, ephemeral=True)

    await ctx.message.add_reaction(dc.reactions.check)

    await inst.update_queue()
    return await dc.edit_long_content(emb, content)


async def play_playlist(message, link: str, inst) -> int:
    # maybe verify link or what idk

    return await cahe.find_playlist_play(message, link, inst)

async def mix(message, prompt, inst, limit=10) -> int:
    await message.add_reaction(dc.reactions.thinking)

    vid = ''
    # get id
    if prompt.startswith("https://"):
        if "list=" in prompt:
            prompt = yt.remove_playlist_from_link(prompt)
        vid = yt.get_id_from_link(prompt)
    else:
        if prompt in cahe.search_cache:
            vid = cahe.search_cache[prompt].link
        else:
            info = yt.get_cache(prompt)
            if info:
                vid = info.link

    playlist_link = f"https://www.youtube.com/watch?v={vid}&list=RD{vid}"

    songs = yt.get_mix_links(playlist_link, limit)
    await message.remove_reaction(dc.reactions.thinking, inst.bot.user)
    return await play_bulk(songs, inst, message)

