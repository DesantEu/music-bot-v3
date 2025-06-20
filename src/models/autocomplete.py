from storage import db
from discord import AutocompleteContext as acctx
from network import ytHandler as yt

class Autocomplete:
    @staticmethod
    async def song(ctx: acctx) -> list[str]:
        print(f"autocomplete got: '{ctx.value}'")
        query = ctx.value

        if query.startswith("https://"):
            query = yt.remove_playlist_from_link(query)
            query = yt.get_id_from_link(query)
            
        return await db.get_song_autocomplete(query)
    

    @staticmethod
    async def local_playlist(ctx: acctx) -> list[str]:
        print(f"autocomplete got: '{ctx.value}'")
        gid = ctx.interaction.guild_id
        if gid is None:
            return []
        return await db.get_lpl_autocomplete(ctx.value, gid)