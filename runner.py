# bot.py
import os

import discord
from dotenv import load_dotenv
import sqlite3
import requests
import urllib
import sys
from discord.ext import tasks

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL'))

intents = discord.Intents.all()

def checkGameStatus():
    try:
        sqliteConnection = sqlite3.connect('marco.db',
                                           detect_types=sqlite3.PARSE_DECLTYPES |
                                                        sqlite3.PARSE_COLNAMES)
        cursor = sqliteConnection.cursor()
        print("Connected to SQLite")
        
        # delete existing. this is stupid, but I made a mistake in table design.
        get_games = """select id, username, gamename from games;"""
        games = []
        cursor.execute(get_games)
        records = cursor.fetchall()
        for row in records:
            query = urllib.parse.quote_plus(row[0])
            print(query)
            r = requests.get('https://tabletop.events/api/librarygame/' + query)

            results = r.json()
            #import pdb; pdb.set_trace()
            if results['result']['is_checked_out'] == 1:
                print("The game is still checked out")
            else:
                print(row[2] + " has been returned. Go go go!")
                #await channel.send("<@{}>, {} has been returned! Go go go!".format(row[1], row[2]))

                delete_query = """delete from games where username = ? and gamename = ?"""
                print(row[0])
                cursor.execute(delete_query, (row[1], row[2]))
                sqliteConnection.commit()
                games.append(row)
                break
                

        cursor.close()
        return games

    except sqlite3.Error as error:
        print("Error while working with SQLite", error)



client = discord.Client(command_prefix='!',intents=intents)

@client.event
async def on_ready():
  
  channel = client.get_channel(1092443478060974200)
  #await channel.send("testing systemd timers instead of cron jobs. Should trigger every minute.")
  myLoop.start(channel)

#   for game in returned_games:
#     pass
    #import pdb; pdb.set_trace()
    # channel = client.get_channel(1156269884020371496)
    # await channel.send("testing systemd timers instead of cron jobs. Should trigger every minute.")
    #import pdb; pdb.set_trace()
    #await channel.send(game + ' is available now!!!! GO GO GO GO!')

@tasks.loop(seconds = 60) # repeat after every 10 seconds
async def myLoop(channel):
  returned_games = checkGameStatus()
  #channel = client.get_channel(CHANNEL_ID)

  for row in returned_games:
    await channel.send("<@{}>, {} has been returned! Go go go!".format(row[1], row[2]))
  #for game in returned_games
  #await channel.send("I figured out why systemd wasn't working. Should trigger every minute.")

  print("looping")


client.run(TOKEN)
