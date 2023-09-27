# bot.py
import os

import discord
from dotenv import load_dotenv
import sqlite3
import requests
import urllib

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = os.getenv('DISCORD_CHANNEL')

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
                games.append(results['result']['name'])

        cursor.close()
        return games

    except sqlite3.Error as error:
        print("Error while working with SQLite", error)
    finally:
        if sqliteConnection:
            sqliteConnection.close()
            print("sqlite connection is closed")



client = discord.Client(command_prefix='!',intents=intents)

@client.event
async def on_ready():
  returned_games = checkGameStatus()
  for game in returned_games:
    channel = client.get_channel(CHANNEL_ID)
    await channel.send("message")
    #import pdb; pdb.set_trace()
    await channel.send(game + ' is available now!!!! GO GO GO GO!')

client.run(TOKEN)