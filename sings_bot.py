# Discord Sings practice bot for Mr Dan's Sings server
# aka jego lohnathan

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
CHANNEL_ID = 842888532988395540
CHANNEL = bot.get_channel(CHANNEL_ID)
# currently test role in my server, should be role that is given to people allowed to start the bot
ALLOWED_ROLE_ID = 843263511043506196
started = False
song_id = 0

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
        songs_data = json.load(read_file)['songs']

    # this stuff is for testing
    # subtract 1 because 0-indexing; maybe change id's to 0-indexed too?
    song_title = songs_data[song_id - 1]['title']
    await ctx.send(song_title)

bot.run(BOT_TOKEN)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if message.channel.id != CHANNEL_ID:
        return
    if not started:
        return
    
#    with open("songs.json", 'r') as read_file:
#        songs_data = json.load(read_file)
#    print(songs_data)
