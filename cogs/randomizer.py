import discord
import random
from discord.ext import commands

class Randomizer(commands.Cog):
	def __init__(self, bot):
		self.bot = bot 

	@commands.command(brief = "Chooses a random argument from the ones you provided")
	async def choose(self, ctx, *args):
		winner = random.choice(args)
		embed = discord.Embed(title = f"The winner is {winner}!  🥳", colour = discord.Colour.purple())
		await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Randomizer(bot))