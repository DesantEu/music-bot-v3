from storage import db
from discord import AutocompleteContext as acctx

class Autocomplete:
    @staticmethod
    async def song(ctx: acctx) -> list[str]:
        print(f"autocomplete got: '{ctx.value}'")
        return await db.get_song_autocomplete(ctx.value)
    

    @staticmethod
    async def local_playlist(ctx: acctx) -> list[str]:
        print(f"autocomplete got: '{ctx.value}'")
        return await db.get_lpl_autocomplete(ctx.value)