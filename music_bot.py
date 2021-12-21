import discord
from discord.ext import commands,tasks
import os
import yt_dlp
import asyncio
import logging


logging.basicConfig(level=logging.INFO)

discord_token = os.getenv("discord_token")

intents = discord.Intents().all()
client = discord.Client(intents=intents)

bot = commands.Bot(command_prefix='!',intents=intents)

yt_dlp.utils.bug_reports_message = lambda: ''

song_queue = []
url_list=[]

def emptydir():
    for item in os.listdir(os.getcwd() + '/downloaded_music'):
        os.remove(os.getcwd() + '/downloaded_music/' + item)

ytdl_format_options = {
    'outtmpl': 'downloaded_music/%(title)s-%(id)s.%(ext)s',
    'format': 'bestaudio/best',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = ""

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]
        filename = data['title'] if stream else ytdl.prepare_filename(data)
        return filename

# implement queue (gf comment never remove)

@bot.command(name='join', help='Tells the bot to join the voice channel')
async def join(ctx):
    if not ctx.message.author.voice:
        await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))
        return
    else:
        channel = ctx.message.author.voice.channel
    await channel.connect()

@bot.command(name='leave', help='To make the bot leave the voice channel')
async def leave(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_connected():
        voice_client.stop()
        await voice_client.disconnect()
        await asyncio.sleep(10)
        emptydir()
    else:
        await ctx.send("The bot is not connected to a voice channel.")

@bot.command(name='play', help='To play song')
async def play(ctx,url):
    if not ctx.message.author.voice:
        await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))
        return
    else:
        voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)

        if not voice_client:          
            voice_channel = ctx.author.voice.channel
            await voice_channel.connect()  
    try :
        server = ctx.message.guild
        voice_channel = server.voice_client
        async with ctx.typing():
            filename = await YTDLSource.from_url(url, loop=bot.loop)
        song_queue.append(filename)
        url_list.append(url)
        await ctx.send('Song has been added to the queue')
        await start_playing(ctx)
    except Exception as e:
        print(e)

async def start_playing(ctx):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if not voice_client.is_playing(): 
        try:
            print('\nThis is the current queue: ' + str(url_list))
            await ctx.send('**Now playing:** {}'.format(url_list.pop(0))) 
            voice_client.play(
                discord.FFmpegPCMAudio(executable="ffmpeg.exe",
                source=song_queue.pop(0)),
                after= lambda e: song_starter(ctx))
        except :
            pass  

def song_starter(ctx):
    starter = start_playing(ctx)
    repeat = asyncio.run_coroutine_threadsafe(starter,client.loop)
    try:
        repeat.result()
    except:
        pass

@bot.command(name='pause', help='This command pauses the song')
async def pause(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_playing():
        voice_client.pause()
    else:
        await ctx.send("The bot is not playing anything at the moment.")
    
@bot.command(name='resume', help='Resumes the song')
async def resume(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_paused():
        voice_client.resume()
    else:
        await ctx.send("The bot was not playing anything before this. Use play_song command")

@bot.command(name='stop', help='Stops the song')
async def stop(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_playing():
        await voice_client.stop()
    else:
        await ctx.send("The bot is not playing anything at the moment.")




bot.run('OTIwMzczMTk2MDAyMzIwNDQ1.YbjaVQ.SzuCq1qNGal6pVw3CWg0NxjQrIg')
