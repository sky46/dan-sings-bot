# Discord Sings practice bot for Mr Dan's Sings server
# aka jego lohnathan

import discord
from discord.ext import commands
from Levenshtein import ratio

import os
from dotenv import load_dotenv
import random
import json
import typing
import re

load_dotenv()
# currently test bot in my server
BOT_TOKEN = os.environ.get("BOT_TOKEN")
intents = discord.Intents(messages=True, guilds=True, members=True, reactions=True)
bot = commands.Bot(command_prefix='-', intents=intents)

# Remember to change this as songs are added
SONGS_COUNT = 2

# currently test role in server, should be role that is given to people allowed to start the bot
ALLOWED_ROLE_ID = 843875380553449524
bot.started = False
bot.song_id = 0
bot.songs_data = {}
bot.next_line = None

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
    # currently test channels in server
    global SINGS_CHANNEL
    global MISTAKES_CHANNEL
    SINGS_CHANNEL = bot.get_channel(843875804588933141)
    MISTAKES_CHANNEL = bot.get_channel(844695429035327488)
    print("We have logged in as jego lohnathan")

@bot.command()
async def start(ctx, song: typing.Optional[int]):
    if ctx.message.author not in ctx.guild.get_role(ALLOWED_ROLE_ID).members:
        return await ctx.send("Sorry, but you don't have permission to start a practice sings.")
        # alternatively just return without any message
        # return
    if song not in range(1, SONGS_COUNT + 1):
        song_id = random.randint(1, SONGS_COUNT)
        if song != None:
            await ctx.send("Invalid song id")
    else:
        song_id = song
    with open("songs.json", 'r') as read_file:
        # subtract 1 because 0-indexing; maybe change id's to 0-indexed too?
        bot.song_data = json.load(read_file)['songs'][song_id - 1]

    # this stuff is for testing
    # subtract 1 because 0-indexing; maybe change id's to 0-indexed too?
    song_title = bot.song_data['title']
    await ctx.send(f"**Now starting practice sings! Song: {song_title}**")
    lyrics_str = '\n'.join(bot.song_data['lyrics'])
    await ctx.send(f"__Lyrics__:\n{lyrics_str}")
    
    bot.started = True

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if message.channel != SINGS_CHANNEL:
        return

    if bot.started and not (message.content.startswith('-') and message.author in
            message.guild.get_role(ALLOWED_ROLE_ID).members):

        if not bot.next_line:
            bot.next_line = 1
            
        try:
            # next_line - 1 cause list zero-indexing
            current_line = bot.song_data['lyrics'][bot.next_line - 1]

            # Remove custom and Unicode emojis
            inputted_line = re.sub(RE_UNICODE_EMOJI, r'', message.content)
            inputted_line = re.sub(RE_CUSTOM_EMOJI, r'', inputted_line)
            
            # Allow emoji-only messages
            if not inputted_line:
                return await MISTAKES_CHANNEL.send("not a mistake but emoji-only message detected")

            # Allow minor errors or differences (80% similarity required) and delete incorrect messages
            if ratio(inputted_line, current_line) >= 0.8:
                bot.next_line += 1
                if bot.song_data['lyrics'][bot.next_line - 1] == "\n":
                    # skip lines that are just newlines
                    bot.next_line += 1
                return
            else:
                await message.delete()
                return await MISTAKES_CHANNEL.send(f"mistake: {message.author} said '{message.content}'")
            
        except IndexError:
            await SINGS_CHANNEL.send("Song completed!")
            bot.started = False

    else:
        await bot.process_commands(message)


bot.run(BOT_TOKEN)