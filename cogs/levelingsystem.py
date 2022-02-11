import discord
from discord.ext import commands
import json
import re

class LevelingSystem(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	async def update_data(self, users, user, guild):
		if not(f"{user.id}@{guild}") in users:
			users[f"{user.id}@{guild}"] = {}
			users[f"{user.id}@{guild}"]['experience'] = 0
			users[f"{user.id}@{guild}"]['level'] = 0
			users[f"{user.id}@{guild}"]['level_end'] = 100

	async def add_experience(self, users, user, guild, exp):
		users[f"{user.id}@{guild}"]['experience'] += exp

	async def level_up(self, users, user, guild, channel):
		experience = users[f"{user.id}@{guild}"]['experience']
		lvl = users[f"{user.id}@{guild}"]['level']
		full_lvl_exp = 5*(lvl**2)+(50*lvl)+100
		if users[f"{user.id}@{guild}"]['level_end'] == experience:
			lvl += 1
			full_lvl_exp = 5*(lvl**2)+(50*lvl)+100
			users[f"{user.id}@{guild}"]['level_end'] = (experience + full_lvl_exp)
			users[f"{user.id}@{guild}"]['level'] = lvl
			with open("cogs/data/users.json", "w") as f:
				json.dump(users, f)
			with open("cogs/data/announcment_channels.json", "r") as f:
				announcment_channels = json.load(f)
			try:
				announcment_channel = self.bot.get_channel(announcment_channels[f"announcment_channel@{guild}"]['id'])
				await announcment_channel.send(f'{user.mention} is now level {lvl}! 🎉')
			except:
				await channel.send(f"{user.mention} is now level {lvl}! 🎉\nYou haven't set an announcment channel on this server!")
			
	@commands.Cog.listener()
	async def on_message(self, message):
		if not message.author.bot:
			with open("cogs/data/users.json", "r") as f:
				users = json.load(f)
			user = message.author
			guild = message.guild.id
			await self.update_data(users, user, guild)
			await self.add_experience(users, user, guild, 5)
			await self.level_up(users, user, guild, message.channel)
			with open("cogs/data/users.json", "w") as f:
				json.dump(users, f)

	@commands.command(brief="Sets the level up announcment channel", description="Admin only command. Sets the channel where the level up announcments will be sent. The argument needs to be the channel's id")
	async def set_announcment_channel(self, ctx, channel_id):
		if ctx.message.author.guild_permissions.administrator:
			with open("cogs/data/announcment_channels.json", "r") as f:
				announcment_channels = json.load(f)
			guild = ctx.guild.id
			if not (f"{channel_id}@{guild}") in announcment_channels:
				announcment_channels[f"announcment_channel@{guild}"] = {}
			announcment_channels[f"announcment_channel@{guild}"]['id'] = int(channel_id)
			with open("cogs/data/announcment_channels.json", "w") as f:
					json.dump(announcment_channels, f)
			await ctx.send("Level up announcment channel set successfully.")
		else:
			await ctx.send("You are not an administrator!")

	@commands.command(brief="Sends yours or another's member level info", description=f"If you want to see your rank, leave the argument empty. If you want to see someone else's rank mention them in the argument. Example: ?rank @User#0001")
	async def rank(self, ctx, *member):
		if member != ():
			try:
				filtered = re.sub("[<>(),@!]", "", member[0])
				user = await self.bot.fetch_user(filtered)
				if user.bot:
					return await ctx.send("Bots don't have levels!")
			except:
				return await ctx.send("Uknown user.")
		else:
			user = ctx.message.author
		guild = ctx.message.guild.id
		with open("cogs/data/users.json", "r") as f:
				users = json.load(f)
		try:
			lvl = users[f"{user.id}@{guild}"]['level']
		except:
			await self.update_data(users, user, guild)
			lvl = users[f"{user.id}@{guild}"]['level']
		lvl_end = users[f"{user.id}@{guild}"]['level_end']
		experience = users[f"{user.id}@{guild}"]['experience']
		experience_needed = (lvl_end - experience)
		embed = discord.Embed(title=f"{user}\n🔹 Level: {lvl}\n🔹 Experience: {experience}\n🔹 Experience needed untin next level: {experience_needed}", colour=discord.Colour.purple())
		await ctx.send(embed=embed)

def setup(bot):
	bot.add_cog(LevelingSystem(bot))