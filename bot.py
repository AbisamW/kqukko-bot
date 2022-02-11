import discord
from discord.ext import commands

bot = commands.Bot(command_prefix = "?")

@bot.event
async def on_ready():
    print(f"{bot.user.name} is ready.")
    bot.load_extension("cogs.music")
    bot.load_extension("cogs.randomizer")
    bot.load_extension("cogs.levelingsystem")
    await bot.change_presence(activity=discord.Game(name=f"{bot.command_prefix}help"))

bot.run("YourTokenHere")
