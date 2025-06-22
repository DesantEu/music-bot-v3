import asyncio
import os
import discord
from core import commands
from core import handler
from storage import db

intents = discord.Intents.default()
intents.members = True


bot = discord.Bot(intents=intents)

@bot.event
async def on_ready():
    if not bot.user is None:
        print(f'{bot.user.name} is up and ready')

        await db.ensure_tables()
        await handler.restore_instances(bot)


@bot.event
async def on_voice_state_update(member, before, after):
    if member == bot.user:
        await handler.handle_voice(member, before, after)


# add commands
bot.add_cog(commands.Player(bot))
bot.add_cog(commands.Playlist(bot))
bot.add_cog(commands.Queue(bot))
bot.add_cog(commands.Admin(bot))

# db.init()


# token = os.environ["DISCORD_TEST_TOKEN"]
token = os.environ["DISCORD_TOKEN"]
try:
    bot.run(token)
except Exception as e:
    print(e)
finally:
    asyncio.run(handler.on_exit())
    