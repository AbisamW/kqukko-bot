import youtube_dl
import discord
from discord.ext import commands
import asyncio

YOUTUBEDL_OPTIONS = {"format" : "bestaudio/best", "quiet" : True, 'default_search': 'auto'}
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
stopped = False

class Player(commands.Cog):
    def __init__(self, bot):
        self.bot = bot 
        self.song_queue = {}

        self.loadself()

    def loadself(self):
        for guild in self.bot.guilds:
            self.song_queue[guild.id] = []

    async def check_queue(self, ctx):
        global stopped
        if ctx.voice_client.is_paused():
            await ctx.voice_client.disconnect()
            del (self.song_queue[ctx.guild.id])[:]
            return await ctx.send("Paused for too long, leaving voice channel.")

        if len(self.song_queue[ctx.guild.id]) > 0:
            song = self.song_queue[ctx.guild.id][0]
            self.song_queue[ctx.guild.id].pop(0)
            await self.play_song(ctx, song)
            
        elif not stopped:
            await ctx.voice_client.disconnect()
            del (self.song_queue[ctx.guild.id])[:]
            return await ctx.send("Song queue is empty, disconnecting.")

    async def search_song(self, amount, song, get_url=False):
        info = await self.bot.loop.run_in_executor(None, lambda: youtube_dl.YoutubeDL(YOUTUBEDL_OPTIONS).extract_info(f"ytsearch{amount}:{song}", download=False, ie_key="YoutubeSearch"))
        if len(info["entries"]) == 0: return None

        return [entry["webpage_url"] for entry in info["entries"]] if get_url else info

    async def play_song(self, ctx, song):
        global stopped
        stopped = False
        with youtube_dl.YoutubeDL(YOUTUBEDL_OPTIONS) as ydl:
            url = ydl.extract_info(song, download=False)
        url2 = url['formats'][0]['url']
        source = await discord.FFmpegOpusAudio.from_probe(url2, **FFMPEG_OPTIONS)
        ctx.voice_client.play(source)
        await ctx.send(f"Now playing: {song}")
        await asyncio.sleep(url['duration'])
        await self.check_queue(ctx)

    @commands.command(brief = "Disconnects the bot from the voice channel")
    async def stop(self, ctx):
        global stopped
        if ctx.voice_client is not None:
            del (self.song_queue[ctx.guild.id])[:]
            stopped = True
            return await ctx.voice_client.disconnect()
        await ctx.send("I'm not connected to a voice channel.")

    @commands.command(brief = "Plays a song", description = "Plays a song, can either take a youtube link or a song name as the argument")
    async def play(self, ctx, *, song=None):  
        if song is None:
            return await ctx.send("No song name or url given.")

        if ctx.author.voice is None:
            return await ctx.send("You're not connected to a voice channel.")

        if ctx.voice_client is None:
            await ctx.author.voice.channel.connect()
        
        elif ctx.author.voice.channel.id != ctx.voice_client.channel.id:
            await ctx.voice_client.disconnect()
            await ctx.author.voice.channel.connect()
        
        if not ("youtube.com/watch?" in song or "https://youtu.be/" in song):
            await ctx.send(f"searching for {song}...")

            result = await self.search_song(1, song, get_url=True)

            if result is None:
                return await ctx.send(f"Song not found. Try searching with for it with the {self.bot.command_prefix}search command.")

            song = result[0]

        if ctx.voice_client.source is not None:
            queue_len = len(self.song_queue[ctx.guild.id])

            if queue_len < 10:
                self.song_queue[ctx.guild.id].append(song)
                return await ctx.send(f"I'm already playing a song, your song was added to the song queue in position: {queue_len+1}.")

            else:
                return await ctx.send("I can only add up to 10 songs to the song queue, try again later.")

        await self.play_song(ctx, song)

    @commands.command(brief = "Searches for song on youtube")
    async def search(self, ctx, *, song=None):
        if song is None: return await ctx.send("No song name or url given.")

        await ctx.send(f'Searching for "{song}"')

        info = await self.search_song(5, song)

        embed = discord.Embed(title=f'Search results for "{song}":', description="*You can use these links to play the song you need.*\n", colour=discord.Colour.purple())
        
        amount = 0
        for entry in info["entries"]:
            embed.description += f"[{entry['title']}]({entry['webpage_url']})\n"
            amount += 1

        embed.set_footer(text=f"Showing the first {amount} results.")
        await ctx.send(embed=embed)

    @commands.command(brief = "Shows the current song queue")
    async def queue(self, ctx):
        if len(self.song_queue[ctx.guild.id]) == 0:
            return await ctx.send("There aren't any songs in the queue at the moment.")

        embed = discord.Embed(title="Song Queue", description="", colour=discord.Colour.purple())
        i = 1
        for url in self.song_queue[ctx.guild.id]:
            with youtube_dl.YoutubeDL(YOUTUBEDL_OPTIONS) as ydl:
                info = ydl.extract_info(url, download=False)
            embed.description += f"[{info['title']}]({info['webpage_url']})\n"
            i += 1

        await ctx.send(embed=embed)

    @commands.command(brief = "Skips the current playing song")
    async def skip(self, ctx):
        if ctx.voice_client is None:
            return await ctx.send("I'm currently not playing any songs.")

        if ctx.author.voice is None:
            return await ctx.send("You're not connected to a voice channel.")

        if ctx.author.voice.channel.id != ctx.voice_client.channel.id:
            return await ctx.send("You're not in the same voice channel as the bot")

        ctx.voice_client.stop()
        await self.check_queue(ctx)

    @commands.command(brief = "Pauses the song")
    async def pause(self, ctx):
        if ctx.voice_client.is_paused():
            return await ctx.send("The song is already paused.")

        ctx.voice_client.pause()
        await ctx.send("The current song has been paused.")

    @commands.command(brief = "Rusumes the song")
    async def resume(self, ctx):
        if ctx.voice_client is None:
            return await ctx.send("I'm not connected to a voice channel.")

        if not ctx.voice_client.is_paused():
            return await ctx.send("The song is already playing.")
        
        ctx.voice_client.resume()
        await ctx.send("The current song has been resumed.")

def setup(bot):
    bot.add_cog(Player(bot))
