from config import TOKEN, INFO_CHANNEL_ID
import discord

from discord.ext import commands
from discord_components import DiscordComponents

from pokemon_command_class import PokemonCommands
from user_command_class import UserCommands

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix='>', intents=intents)
DiscordComponents(bot)

@bot.event
async def on_ready():
    print('я зол😡')
    p_commands.info_channel = bot.get_channel(INFO_CHANNEL_ID)
    bot.loop.create_task(p_commands.start_world())

u_commands = UserCommands(bot)
p_commands = PokemonCommands(bot, u_commands)
bot.add_cog(p_commands)
bot.add_cog(u_commands)
bot.run(TOKEN)
