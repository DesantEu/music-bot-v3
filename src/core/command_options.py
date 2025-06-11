from discord import Option
from discord import SlashCommandOptionType as scot
from storage.cacheHandler import get_autocomplete

play = [
    Option(description="песя", name="asdasdasd", autocomplete=get_autocomplete)
]