import asyncio
import discord
from discord import ApplicationContext as actx
from models.long_message import LongMessage
from models.enums import reactions

# TODO: 
# theres a lot of returns that only return 0 maybe add some checks or smth

color_pink = discord.Colour.from_rgb(226, 195, 205)
# color_pink_old = discord.Color.from_rgb(255, 166, 201)


messages:dict[int, discord.Message] = {}
long_messages:dict[int, LongMessage] = {}

async def send(msg:str, ctx: actx, color=color_pink, ephemeral=False, respond=True) -> int:
    if msg == '':
        emb = discord.Embed()
    else:
        emb = discord.Embed(title=msg)
    emb.color = color
    if respond:
        interaction = await ctx.send_response(embed=emb, ephemeral=ephemeral)
        if interaction.message: 
            messages[interaction.message.id] = interaction.message
            return interaction.message.id
    else:
        message = await ctx.channel.send(embed=emb) 
        messages[message.id] = message
        return message.id
    return -1

async def send_long(title:str, smaller_title:str, content:list[tuple[str, str]], ctx: actx, color=color_pink, ephemeral=False, respond=True) -> int:
    global long_messages

    msg = LongMessage(title, smaller_title, content)
    await msg.send(ctx, color, respond, ephemeral)
    long_messages[msg.message.id] = msg
    return msg.message.id


async def edit_long_status(id, index:int, value:str) -> int:
    await long_messages[id].edit(index, status=value) # TODO: this could be better some day
    return 0

async def edit_long_text(id, index: int, value: str) -> int:
    await long_messages[id].edit(index, text=value)
    return 0

async def edit_long_both(id, index: int, status: str, text: str) -> int:
    await long_messages[id].edit(index, status=status, text=text)
    return 0

async def edit_long_content(id, content:list[tuple[str, str]]) -> int:
    await long_messages[id].setContent(content)
    return 0

async def edit_long_title(id, title: str) -> int:
    await long_messages[id].edit(0, title=title)
    return 0

async def edit_long_smaller_title(id, smaller_title: str) -> int:
    await long_messages[id].edit(0, smaller_title=smaller_title)
    return 0

async def edit(id, title:str, body:dict[str,str]={}, color=color_pink):
    if id in messages:
        emb = discord.Embed(title=title)
        if not body == {}:
            for i in body:
                emb.add_field(name=i, value=body[i])

        emb.color = color
                
        messages[id] = await messages[id].edit(embed=emb)

# adds a field to an embed
async def add_status(id, name, value) -> int:
    if not id in messages or len(messages[id].embeds) == 0:
        return -1

    emb = messages[id].embeds[0].add_field(name=name, value=value)
    messages[id] = await messages[id].edit(embed=emb)

    return len(messages[id].embeds[0].fields) - 1


async def edit_status(id, ind, value) -> int:
    if not id in messages or len(messages[id].embeds) == 0 or ind > len(messages[id].embeds[0].fields) - 1:
        return -1

    name = messages[id].embeds[0].fields[ind].name

    emb = messages[id].embeds[0].set_field_at(ind, name=name, value=value)
    messages[id] = await messages[id].edit(embed=emb)
    return 0


async def edit_status_title(id, ind, name) -> int:
    if not id in messages or len(messages[id].embeds) == 0 or ind > len(messages[id].embeds[0].fields) - 1:
        return -1

    value = messages[id].embeds[0].fields[ind].value

    emb = messages[id].embeds[0].set_field_at(ind, name=name, value=value)
    messages[id] = await messages[id].edit(embed=emb)
    return 0


async def set_footer(id, value) -> int:
    if id in long_messages:
        return -1
    if not id in messages or len(messages[id].embeds) == 0:
        return -1

    emb = messages[id].embeds[0].set_footer(text=value)
    messages[id] = await messages[id].edit(embed=emb)
    return 0


def isInVC(author):
    return type(author) == discord.Member and not author.voice is None


async def check_cross(ctx: actx, res: bool):
    if res:
        await ctx.send_response(reactions.check, ephemeral=True)
        await asyncio.sleep(1)
        await ctx.interaction.delete_original_response()
    else:
        await ctx.send_response(reactions.cross, ephemeral=True)
        await asyncio.sleep(5)
        await ctx.interaction.delete_original_response()

