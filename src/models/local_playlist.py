from typing import Self
from storage import db
from models.song import Song


class LocalPlaylist:
    def __init__(self, name: str, gid: int, song_ids: list[str] = []):
        self.title: str = name
        self.songs: list[Song] = []
        self.gid = gid


    def get_content(self) -> list[tuple[str, str]]:
        content = []

        for i in range(len(self.songs)):
            content.append((f"{i}. ", self.songs[i].title))

        return content
    

    def get_links(self) -> list[str]:
        return ["https://www.youtube.com/watch?v=" + i.id for i in self.songs]
    

    def get_ids(self) -> list[str]:
        return [i.id for i in self.songs]


    async def save(self) -> bool:
        ids = self.get_ids()
        if ids == []:
            return False
        
        await db.add_local_playlist(self.gid, self.title, ids)

        return True


    async def load(self) -> Self:
        song_info = await db.get_local_playlist_songs(self.gid, self.title)
        for id, title in song_info:
            self.songs.append(Song.from_info(title, id))

        return self


# async def play_playlist(ctx: actx, name, inst) -> int:
#     # handle empty prompts
#     if name == '':
#         await ctx.send_response(dc.reactions.fyou, ephemeral=True)
#         return -1

#     # check if the user is in a vc
#     if not dc.isInVC(ctx.user):
#         await ctx.send_response(loc.no_vc, ephemeral=True)
#         return -1


#     # check if playlist exists
#     if not os.path.exists(f'playlists/{name}.lpl'):
#         await ctx.send_response(loc.playlist_not_found, ephemeral=True)
#         return -1

#     # open the playlist
#     with open(f'playlists/{name}.lpl', 'r') as file:
#         try:
#             playlist:dict = json.loads(file.read())
#         except:
#             await ctx.send_response(loc.playlist_broken, ephemeral=True)
#             return -1
            

#         # notify the server
#         emb = await dc.send_long(loc.playlist_on, name, [['-', i] for i in playlist], ctx, ephemeral=True)
#         song_available = False
#         tried_connecting = False

#         # add songs to queue
#         for song in playlist:
#             ind = list(playlist).index(song)
#             # first try the links
#             if await cahe.find_link_play(ctx, playlist[song], inst, silent=True, skipQueueUpdate=True) == 0:
#                 await dc.edit_long_status(emb, ind, f'{inst.queue.len()}.  ')
#                 song_available = True
#             # if the link fails try to find by name
#             else:
#                 await dc.edit_long_status(emb, ind, 'V')
#                 if await cahe.find_prompt_play(ctx, song, inst, silent=True, skipQueueUpdate=True) == 0:
#                     await dc.edit_long_status(emb, ind, f'{inst.queue.len()}.  ')
#                     song_available = True
#                 # if everything fails theres nothing we can do really
#                 else:
#                     await dc.edit_long_status(emb, ind, 'X')

#             # if nothing is playing we should start playing i guess
#             if song_available and not tried_connecting:
#                 tried_connecting = True
#                 # check vc again just to be sure
#                 if not dc.isInVC(ctx.user):
#                     await ctx.send_response(loc.left_vc)
#                     return -1
#                 else:
#                     await dc.join(ctx, inst)
#                     if not inst.isPlaying:
#                         player.play_from_queue(0, inst) # TODO: remove

#         # check vc again just for fun
#         if not dc.isInVC(ctx.user):
#             await ctx.send_response(loc.left_vc, ephemeral=True)

#         # await dc.add_status(emb, loc.playlist_success, dc.reactions.pls_tears)
#         # await ctx.message.add_reaction(dc.reactions.check)
#         await inst.update_queue()

#         return 0


# async def save_playlist(ctx: actx, name, inst):
#     # handle empty prompts
#     if name == '' or inst.queue.len() == 0:
#         await ctx.send_response(dc.reactions.fyou, ephemeral=True)
#         return -1


#     if os.path.exists(f'playlists/{name}.lpl'): # TODO: THIS IS NOT AN EMBED CHANGE THIS
#         emb = await ctx.send_response(loc.playlist_rewrite + name)
#     else:
#         emb = await ctx.send_response(loc.playlist_saving + name)

#     try:
#         with open(f'playlists/{name}.lpl', 'w+') as file:
#             file.write(inst.queue.toJsonStr())
#         await dc.add_status(emb, dc.reactions.thumbs_up, dc.reactions.cold)
#     except:
#         await dc.add_status(emb, dc.reactions.cross, dc.reactions.hot)


# async def list_playlists(ctx: actx, name: str):
#     path = 'playlists'
#     filepath = f'playlists/{name}.lpl'
#     # list all files
#     if name == '':
#         files = [f[:-4] for f in os.listdir(path) if f.endswith('.lpl')]
#         await dc.send_long(loc.playlists, '', [['>', i] for i in files], ctx, ephemeral=True)
#     # list specific playlist
#     else:
#         # if doesnt exist
#         if not os.path.exists(filepath):
#             await ctx.send_response(dc.reactions.cross, ephemeral=True)
#             return -1
#         # if does exist
#         else:
#             with open(filepath, 'r', encoding='utf-8') as file:
#                 try:
#                     playlist:dict = json.loads(file.read())
#                 except:
#                     await ctx.send_response(loc.playlist_broken, ephemeral=True)
#                     return -1

#             await dc.send_long(loc.playlist_content, name, [['>', i] for i in playlist], ctx, ephemeral=True)
#                 # await dc.send_long(str(songs), message.channel, title=f'Плейлист {name}:')

# def get_autocomplete(ctx) -> list[str]:
#     print(f"autocomplete got: '{ctx.value}'")
    
#     path = 'playlists'
#     files = [f[:-4] for f in os.listdir(path) if f.endswith('.lpl')]

#     return [i for i in files if i.startswith(ctx.value)]
