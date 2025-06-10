from network import dcHandler as dc
import discord
from locales import bot_locale as loc

class Player:
    def __init__(self, inst):
        self.message:discord.Message
        self.isStopped = False
        self.isEmpty = True
        self.song = loc.song_empty
        self.time = '(0:00/0:00)'
        self.inst = inst
        self.next = dc.reactions.fyou
        

    async def update(self):
        pass

    async def update_embed(self):
        await self.message.edit(embed=self.genEmbed())

    def genEmbed(self) -> discord.Embed:
        emb = discord.Embed(title=loc.now_playing)
        emb.color = discord.Color.from_str("#b19cd9")
        emb.add_field(name=self.song, value=self.time)
        if not self.isEmpty:
            emb.set_footer(text=self.next)

        return emb

    async def stop(self):
        self.isStopped = True
        self.time = ""
        self.inst.hasPlayer = False
        await self.update_embed()


async def send_np(channel, inst):
    # stop the old player from updating
    if inst.hasPlayer:
        await inst.player.stop()
    # add a player
    inst.player = Player(inst)
    inst.hasPlayer = True

    inst.player.message = await channel.send(embed=inst.player.genEmbed())

