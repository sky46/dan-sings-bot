# Discord Sings practice bot for Mr Dan's Sings server
# aka jego lohnathan
# by skytheguy#3630

import discord
from discord.ext import commands
from Levenshtein import ratio

import os
from math import ceil
from dotenv import load_dotenv
import random
import json
import typing
import re
import more_itertools
import asyncio

load_dotenv()
BOT_TOKEN = os.environ.get("BOT_TOKEN")
intents = discord.Intents(messages=True, guilds=True, members=True, reactions=True, voice_states=True)
bot = commands.Bot(command_prefix='?', intents=intents)

with open("songs.json", 'r') as read_file:
    data = json.load(read_file)
    SONGS_COUNT = len(data['songs'])
    bot.songs = data['songs']

# Role that's allowed to start practice sings
bot.ALLOWED_ROLE_ID = int(os.environ.get("ALLOWED_ROLE"))

bot.song_id = 0
bot.started = False
bot.songs_data = {}
bot.next_line = None
bot.mistakes = 0

# Role that's given when joining VC
bot.VC_ROLE_ID = int(os.environ.get("VC_ROLE"))

bot.remove_command('help')

# Regex to find unicode emojis
# Ref: https://gist.github.com/Alex-Just/e86110836f3f93fe7932290526529cd1#gistcomment-3208085
# Ref: https://en.wikipedia.org/wiki/Unicode_block
RE_UNICODE_EMOJI = re.compile(
    "(["
    "\U0001F1E0-\U0001F1FF"  # flags (iOS)
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F680-\U0001F6FF"  # transport & map symbols
    "\U0001F700-\U0001F77F"  # alchemical symbols
    "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
    "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
    "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
    "\U0001FA00-\U0001FA6F"  # Chess Symbols
    "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
    "\U00002702-\U000027B0"  # Dingbats
    "])"
)

RE_CUSTOM_EMOJI = r"<:\w+:\d+>"


@bot.event
async def on_ready():
    # Channel to do sings commands and practice sings
    bot.SINGS_CHANNEL = bot.get_channel(int(os.environ.get("SINGS_CHANNEL")))
    # Channel to print lyrics
    bot.LYRICS_CHANNEL = bot.get_channel(int(os.environ.get("LYRICS_CHANNEL")))
    # VC that gives role when joined
    bot.ROLE_CHANNEL = bot.get_channel(int(os.environ.get("ROLE_CHANNEL")))
    print("We have logged in as jego lohnathan")

@bot.command()
async def help(ctx):
    embed = discord.Embed(title="Jego Lohnathan Help", colour=0xb022cb)
    allowed_role = ctx.guild.get_role(bot.ALLOWED_ROLE_ID)
    embed.add_field(name=f"** **\nTo start a practice sings, use `?start [song id]`! You must have the `{allowed_role.name}` role.",
        value="If no `song id` is provided, it will pick a random song.", inline=False)
    embed.add_field(name=f"** **\nOnce a song is started, get the next line from {bot.SINGS_CHANNEL.name}!",
        value="Minor typos and emoji are allowed.", inline=False)
    embed.add_field(name="When a song finishes, it'll randomly choose another song to start.",
        value=f"Use `?stop` to stop the practice sings (you must have the {allowed_role.name} role).")
    embed.add_field(name="** **", value="Bot by skytheguy#3630 for Mr Dan Discord Sings server", inline=False)
    await ctx.send(embed=embed)

async def start_sings(song=None):
    bot.next_line = None
    bot.mistakes = 0

    if song != None:
        try:
            song = int(song)
        except (TypeError, ValueError):
            return await bot.SINGS_CHANNEL.send("Invalid song id")

    if song not in range(1, SONGS_COUNT + 1):
        if song:
            return await bot.SINGS_CHANNEL.send("Invalid song id")
        song_id = random.randint(1, SONGS_COUNT)
    else:
        song_id = song

    bot.song_data = bot.songs[song_id - 1]

    song_title = bot.song_data['title']
    song_artist = bot.song_data['artist']

    lyrics_embed = discord.Embed(title="__Now starting practice sings!__", colour=0xb022cb)
    lyrics_embed.add_field(name=song_title, value=f"By {song_artist}")
    info_embed = discord.Embed(title=f"__New practice sings started!__", colour=0xb022cb)
    info_embed.add_field(name=song_title, value=f"By {song_artist}")

    await bot.SINGS_CHANNEL.send(embed=info_embed)
    bot.started = True

    lyrics_list = list(more_itertools.split_at(bot.song_data['lyrics'], lambda x: x == ""))
    lyrics_list = ["\n".join(lines) for lines in lyrics_list]

    next_line_embed = discord.Embed(title=song_title, colour=0x0f5fbc)
    next_line_embed.add_field(name="Next line", value=bot.song_data['lyrics'][0])

    def is_me(message):
        return message.author == bot.user
    await bot.LYRICS_CHANNEL.purge(check=is_me)

    await bot.LYRICS_CHANNEL.send(embed=lyrics_embed)
    await bot.LYRICS_CHANNEL.send(f"Lyrics:")

    for lines in lyrics_list:
        await bot.LYRICS_CHANNEL.send(f"** **\n{lines}")
        await asyncio.sleep(1)

    bot.next_line_message = await bot.LYRICS_CHANNEL.send(embed=next_line_embed)

@bot.command()
async def start(ctx, song=None):
    if ctx.message.author not in ctx.guild.get_role(bot.ALLOWED_ROLE_ID).members:
        return await ctx.send("Sorry, but you don't have permission to start practice sings.")
    
    if bot.started:
        return

    await start_sings(song)

@bot.command()
async def stop(ctx):
    if ctx.message.author not in ctx.guild.get_role(bot.ALLOWED_ROLE_ID).members:
        return
    if bot.started == False:
        return await ctx.send("No currently running practice sings")

    def is_me(message):
        return message.author == bot.user
    await bot.LYRICS_CHANNEL.purge(check=is_me)

    embed = discord.Embed(title="Stopped practice sings", colour=0xbd1800)
    embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
    await ctx.send(embed=embed)
    bot.started = False

@bot.command(name="songs")
async def list_songs(ctx, page=1):
    pages = ceil(len(bot.songs) / 25)
    if page not in range(1, pages + 1):
        return await ctx.send("Invalid page number")
    
    embed = discord.Embed(title=f"Available songs (page {page} of {pages})", colour=0xb022cb)
    embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)

    for song in bot.songs[(page - 1) * 25 : page * 25]:
        embed.add_field(name=f"{song['id']}: {song['title']} by {song['artist']}", value=song['url'], inline=False)

    await ctx.send(embed=embed)
    await ctx.send("Use `?start [song number]` to start a practice sings!\ne.g. `?start 3` for The Duck Song.")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if message.channel != bot.SINGS_CHANNEL:
        return
    if message.content.lower() == "$kill" and message.author.id == 682778479229403136:
        await bot.close()

    if bot.started and not (message.content.startswith('?') and message.author in
            message.guild.get_role(bot.ALLOWED_ROLE_ID).members):

        if not bot.next_line:
            bot.next_line = 1
            # next_line - 1 cause list zero-indexing
            bot.current_line = bot.song_data['lyrics'][bot.next_line - 1]


        # Remove custom and Unicode emojis
        inputted_line = re.sub(RE_UNICODE_EMOJI, r'', message.content)
        inputted_line = re.sub(RE_CUSTOM_EMOJI, r'', inputted_line)
        
        # Allow emoji-only messages
        if not inputted_line:
            return

        # Allow minor errors or differences (80% similarity required) and delete incorrect messages
        if ratio(inputted_line.lower(), bot.current_line.lower()) >= 0.8:
            bot.next_line += 1

            try:
                bot.current_line = bot.song_data['lyrics'][bot.next_line - 1]
                if bot.current_line == "":
                    # skip lines that are just newlines
                    bot.next_line += 1
                    bot.current_line = bot.song_data['lyrics'][bot.next_line - 1]
                    
                next_line_embed = discord.Embed(title=bot.song_data['title'], colour=0x0f5fbc)
                next_line_embed.add_field(name="Next line", value=bot.current_line)
                await bot.next_line_message.edit(embed=next_line_embed)
                
            except IndexError:
                embed = discord.Embed(title="Song completed!", colour=0xb022cb)
                embed.add_field(name=f"{bot.song_data['artist']} - {bot.song_data['title']}",
                    value=f"We made {bot.mistakes} mistakes.")
                await bot.SINGS_CHANNEL.send(embed=embed)
                await start_sings()

        else:
            await message.delete()
            bot.mistakes += 1
            mistake_embed = discord.Embed(colour=0xbd1800)
            mistake_embed.add_field(name="Mistake", value=f"{message.author} said '{message.content}'")
            return await message.author.send(embed=mistake_embed)
            
    await bot.process_commands(message)

# @bot.event
# async def on_voice_state_update(member, before, after):
#     role = discord.utils.get(member.guild.roles, id=bot.VC_ROLE_ID)
#     if before.channel != bot.ROLE_CHANNEL and after.channel == bot.ROLE_CHANNEL:
#         await member.add_roles(role)
#     elif before.channel == bot.ROLE_CHANNEL and after.channel != bot.ROLE_CHANNEL:
#         await member.remove_roles(role)

@bot.event
async def on_message_edit(before, after):
    allowed_role = before.guild.get_role(bot.ALLOWED_ROLE_ID)
    if allowed_role in before.author.roles:
        return
    else:
        await after.delete()

bot.run(BOT_TOKEN)
