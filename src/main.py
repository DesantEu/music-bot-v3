import os
import discord
from core import commands
from core import handler
from storage import db


bot = discord.Bot()

@bot.event
async def on_ready():
    if not bot.user is None:
        print(f'{bot.user.name} is up and ready')

        await db.ensure_tables()


@bot.event
async def on_voice_state_update(member, before, after):
    if member == bot.user:
        await handler.handle_voice(member, before, after)


# add commands
bot.add_cog(commands.User(bot))
bot.add_cog(commands.Admin(bot))

# db.init()


# token = os.environ["DISCORD_TEST_TOKEN"]
token = os.environ["DISCORD_TOKEN"]
bot.run(token)