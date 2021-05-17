# Discord Sings practice bot for Mr Dan's Sings server
# aka jego lohnathan

from asyncio import windows_events
import discord
from discord.ext import commands

import os
from dotenv import load_dotenv
import random
import json
import typing

load_dotenv()
# currently test bot in my server
BOT_TOKEN = os.environ.get("BOT_TOKEN")
intents = discord.Intents(messages=True, guilds=True, members=True, reactions=True)
bot = commands.Bot(command_prefix='-', intents=intents)

# Remember to change this as songs are added
SONGS_COUNT = 2

# currently this is a test channel in my server
CHANNEL_ID = 843875804588933141
# currently test role in my server, should be role that is given to people allowed to start the bot
ALLOWED_ROLE_ID = 843875380553449524
bot.started = False
bot.song_id = 0
bot.songs_data = {}
bot.next_line = None

@bot.event
async def on_ready():
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
    await ctx.send(f"Now starting practice sings! Song: {song_title}")
    
    bot.started = True
    print(bot.started)


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if message.channel.id != CHANNEL_ID:
        print('wrong channel')
        return

    if bot.started:
        if not bot.next_line:
            bot.next_line = 1
        bot.lyrics = bot.song_data['lyrics']
        # line - 1 cause list zero-indexing
        try:
            await message.channel.send(bot.lyrics[bot.next_line - 1])
            bot.next_line += 1
        except IndexError:
            await message.channel.send("Song completed!")
            bot.started = False

    await bot.process_commands(message)


bot.run(BOT_TOKEN)