
import discord
from models.enums import reactions
from locales import bot_locale as loc
from discord import ApplicationContext as actx
from discord.ui.button import Button

color_pink = discord.Colour.from_rgb(226, 195, 205)

class LongMessage:
    def __init__(self, title:str, smaller_title:str, content:list[tuple[str, str]], page=0):
        self.page:int = page
        self.pages:list[str] = []
        self.title = title
        self.smaller_title = smaller_title
        self.content = content
        self.isMultipage = False

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

        await self.message.edit(embed=self.genEmbed(), view=QueueButtonsView(self) if self.isMultipage else None);


    async def send(self, ctx: actx, color=color_pink, respond=False, ephemeral=False):
        if respond:
            interaction = await ctx.send_response(embed=self.genEmbed(color=color), ephemeral=ephemeral)
            self.message = interaction
        else:
            self.message = await ctx.channel.send(embed=self.genEmbed(color=color))
        # await self.refreshReactions()


    async def parse_reaction(self, reaction):
        """ Parses the reaction and changes the page if necessary.
        Returns:
            -1 if the reaction was not handled
            0 if the page was changed
            1 if the page was not changed
            -2 if the reaction was not a page change reaction
        """
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
            await self.message.edit(embed=self.genEmbed(), view=QueueButtonsView(self) if self.isMultipage else None)
            return 0
        return -1
    
        
    async def setContent(self, content:list[tuple[str, str]]):
        self.content = content
        self.regenerate()
        await self.message.edit(embed=self.genEmbed(), view=QueueButtonsView(self) if self.isMultipage else None)
        return 0

    def append(self):
        return


    def __str__(self):
        return ''
    

class QueueButtonsView(discord.ui.View):
    def __init__(self, long_message: LongMessage):
        super().__init__(timeout=None)
        self.long_message = long_message
        self.left = discord.ui.Button(emoji=reactions.left_arrow, style=discord.ButtonStyle.blurple, disabled=self.long_message.page == 0)
        self.left.callback = self.on_left_click
        self.right = discord.ui.Button(emoji=reactions.right_arrow, style=discord.ButtonStyle.blurple, disabled=self.long_message.page == len(self.long_message.pages) - 1)
        self.right.callback = self.on_right_click
        self.add_item(self.left)
        self.add_item(self.right)


    async def on_left_click(self, interaction: discord.Interaction):
        res = await self.long_message.parse_reaction(reactions.left_arrow)
        
        self.update_buttons()

        await interaction.response.edit_message(embed=self.long_message.genEmbed(), view=self if self.long_message.isMultipage else None)


    async def on_right_click(self, interaction: discord.Interaction):
        res = await self.long_message.parse_reaction(reactions.right_arrow)

        self.update_buttons()

        await interaction.response.edit_message(embed=self.long_message.genEmbed(), view=self if self.long_message.isMultipage else None)


    def update_buttons(self):
        """ Updates the buttons based on the current page. """

        # disable left button if on first page, right button if on last page
        if self.long_message.page == 0:
            self.left.disabled = True
        else:
            self.left.disabled = False
        if self.long_message.page == len(self.long_message.pages) - 1:
            self.right.disabled = True
        else:
            self.right.disabled = False

