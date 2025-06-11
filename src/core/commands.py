# from main import bot
from discord.commands import option 
from discord import ApplicationContext as actx
from discord import SlashCommand, MessageCommand
from core import handler
from core import command_options as opts
from playback import player


async def play(ctx: actx, song: str):
    inst = await handler.getInstance(ctx.guild_id, ctx.bot)
    await player.play(ctx, song, inst)

cmd_play = SlashCommand(play, name="play2", description="музыза", options=opts.play)




