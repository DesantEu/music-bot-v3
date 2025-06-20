import asyncio
import discord
from discord import ApplicationContext as actx
from locales import bot_locale as loc

# TODO: 
# theres a lot of returns that only return 0 maybe add some checks or smth

color_pink = discord.Colour.from_rgb(226, 195, 205)
# color_pink_old = discord.Color.from_rgb(255, 166, 201)

class LongMessage:
    def __init__(self, title:str, smaller_title:str, content:list[tuple[str, str]], page=0):
        self.page:int = page
        self.pages:list[str] = []
        self.title = title
        self.smaller_title = smaller_title
        self.content = content
        self.isMultipage = False
        self.hasReactions = False #TODO: there must be a way to avoid this

        self.message: discord.Message | discord.Interaction

        self.regenerate()


    def regenerate(self):
        char_limit = 1024
        # handle multipage
        if len('\n'.join([f'{i[0]} {i[1]}' for i in self.content])) > char_limit:
            self.pages.clear()
            line = 0
            page = 0
            
            # generate pages
            self.pages.append('')
            while line < len(self.content):
                while line < len(self.content) and len(self.pages[page]) + len(f'{self.content[line][0]} {self.content[line][1]}') + 1 < char_limit:
                    newline =  f'{self.content[line][0]} {self.content[line][1]}\n'
                    self.pages[page] += newline
                    line += 1
                page += 1
                self.pages.append('')
            self.isMultipage = True
            self.pages.pop(-1)

        # handle single page
        else:
            self.page = 0
            self.pages.clear()

            self.pages.append('\n'.join([f'{i[0]} {i[1]}' for i in self.content]))

            self.isMultipage = False


    def genEmbed(self, color=color_pink):
        emb = discord.Embed(title=self.title)
        emb.color = color
        emb.add_field(name=self.smaller_title, value=self.pages[self.page])
        if self.isMultipage:
            emb.set_footer(text=f'{loc.page} {self.page + 1}')

        return emb


    async def edit(self, ind, status='', text='', title='', smaller_title=''):
        if not status == '':
            self.content[ind][0] = status

        if not text == '':
            self.content[ind][1] = text

        if not title == '':
            self.title = title

        if not smaller_title == '':
            self.smaller_title = smaller_title

        self.regenerate()

        await self.message.edit(embed=self.genEmbed());


    async def send(self, ctx: actx, color=color_pink, respond=False, ephemeral=False):
        if respond:
            interaction = await ctx.send_response(embed=self.genEmbed(color=color), ephemeral=ephemeral)
            self.message = interaction
        else:
            self.message = await ctx.channel.send(embed=self.genEmbed(color=color))
        # await self.refreshReactions()


    async def parse_reaction(self, reaction):
        if not reaction == reactions.left_arrow and not reaction == reactions.right_arrow:
            return -2
        if not self.isMultipage:
            return 1

        changed = False
        if reaction == reactions.left_arrow:
            if not self.page < 1:
                self.page -= 1
                changed = True
            else:
                return 1

        elif reaction == reactions.right_arrow:
            if not self.page == len(self.pages) - 1:
                self.page += 1
                changed = True
            else:
                return 1

        if changed:
            self.regenerate()
            await self.message.edit(embed=self.genEmbed())
            return 0
        return -1

    # async def refreshReactions(self):
    #     if self.isMultipage and not self.hasReactions:
    #         await self.message.clear_reaction(reactions.right_arrow)
    #         await self.message.clear_reaction(reactions.left_arrow)
    #         await self.message.add_reaction(reactions.left_arrow)
    #         await self.message.add_reaction(reactions.right_arrow)
    #         self.hasReactions = True

    #     if not self.isMultipage and self.hasReactions:
    #         await self.message.clear_reaction(reactions.right_arrow)
    #         await self.message.clear_reaction(reactions.left_arrow)
    #         self.hasReactions = False
        
    async def setContent(self, content:list[tuple[str, str]]):
        self.content = content
        self.regenerate()
        await self.message.edit(embed=self.genEmbed())
        # await self.refreshReactions()
        return 0

    def append(self):
        return


    def __str__(self):
        return ''

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


class reactions:
    check = '✅'
    cross = '❌'
    warn = '⚠️'
    fyou = '🖕'
    wave = '👋'
    thumbs_up = '👍'
    thinking = '🧠'
   
    cold = '🥶'
    hot = '🥵'
    mew1 = '🤫'
    mew2 = '🧏'

    pls ='🥺'
    pls_tears = '🥹'

    black_circle = '⚫'
    green_circle = '🟢'
    yellow_circle = '🟡'
    orange_circle = '🟠'
    red_circle = '🔴'

    left_arrow = '⬅️'
    right_arrow = '➡️'
    down_arrow = '⬇️'
    play = '▶️'

    internet = '🌐'
    search = '🔍'
    folder = '📁'
    
    


