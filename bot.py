# bot.py
import os
import random
import discord
import sqlite3
from discord.ext import commands
from dotenv import load_dotenv
import datetime
import urllib
import requests

MOCK_CHECKOUT = True

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = os.getenv('DISCORD_CHANNEL')
intents = discord.Intents.all()


def getUsers():
    try:
        sqliteConnection = sqlite3.connect('marco.db',
                                           detect_types=sqlite3.PARSE_DECLTYPES |
                                                        sqlite3.PARSE_COLNAMES)
        cursor = sqliteConnection.cursor()
        print("Connected to SQLite")

        # get developer detail
        sqlite_select_query = """SELECT username, whereabouts, time from users"""
        cursor.execute(sqlite_select_query)
        records = cursor.fetchall()

        #import pdb; pdb.set_trace()
        for row in records:
        #     developer = row[0]
          joining_Date = row[2]
        #     print(developer, " joined on", joiningDate)
          print("joining date type is", type(joining_Date))

        cursor.close()
        return records

    except sqlite3.Error as error:
        print("Error while working with SQLite", error)
    finally:
        if (sqliteConnection):
            sqliteConnection.close()
            print("sqlite connection is closed")

def trackGame(id, username, gamename):
    try:
        sqliteConnection = sqlite3.connect('marco.db',
                                           detect_types=sqlite3.PARSE_DECLTYPES |
                                                        sqlite3.PARSE_COLNAMES)
        cursor = sqliteConnection.cursor()
        print("Connected to SQLite")
        
        # delete existing. this is stupid, but I made a mistake in table design.

        sqlite_insert_with_param = """INSERT INTO 'games'
                          ('id', 'username', 'gamename') 
                          VALUES (?, ?, ?);"""
        
        data_tuple = (id, username, gamename)

        cursor.execute(sqlite_insert_with_param, data_tuple)
        sqliteConnection.commit()
        print("Game added successfully \n")

        cursor.close()

    except sqlite3.Error as error:
        print("Error while working with SQLite", error)
    finally:
        if sqliteConnection:
            sqliteConnection.close()
            print("sqlite connection is closed")

def checkinUser(name, whereabouts, joiningDate):
    try:
        sqliteConnection = sqlite3.connect('marco.db',
                                           detect_types=sqlite3.PARSE_DECLTYPES |
                                                        sqlite3.PARSE_COLNAMES)
        cursor = sqliteConnection.cursor()
        print("Connected to SQLite")
        
        # delete existing. this is stupid, but I made a mistake in table design.
        delete_existing_entry = """DELETE FROM users where username = (?);"""

        print(name)
        cursor.execute(delete_existing_entry, (name,))
        sqliteConnection.commit()
        # insert developer detail
        sqlite_insert_with_param = """INSERT INTO 'users'
                          ('username', 'whereabouts', 'time') 
                          VALUES (?, ?, ?);"""
        #location = "".join(ch for ch in whereabouts if ch.isalnum())
        location = whereabouts
        data_tuple = (name, location, joiningDate)
        #print(data_tuple)
        cursor.execute(sqlite_insert_with_param, data_tuple)
        sqliteConnection.commit()
        print("Developer added successfully \n")

        cursor.close()

    except sqlite3.Error as error:
        print("Error while working with SQLite", error)
    finally:
        if sqliteConnection:
            sqliteConnection.close()
            print("sqlite connection is closed")

bot = commands.Bot(command_prefix='!',intents=intents)

@bot.command(name='checkin', help='Checkin to an arbitrary location.')
async def checkin(ctx, *location):
    mystr = ' '.join(location)
    timestamp = datetime.datetime.now()
    checkinUser(ctx.author.global_name, mystr, timestamp)
    #import pdb; pdb.set_trace()

    msg = "{} checked in with: '{}' at {}".format(ctx.author.global_name, mystr, timestamp.strftime('%H:%M'))
    await ctx.send(msg)

@bot.command(name='marco', help='See where everyone is hanging.')
async def marco(ctx):
    timestamp = datetime.datetime.now()
    users = getUsers()
    now = datetime.datetime.now()
    for user in users:
        timediff =int(((now - user[2]).total_seconds()) / 60)
        msg = "{} last checked in with: {}, {} minutes ago".format(user[0], user[1], timediff)
        await ctx.send(msg)
    return

@bot.command(name='iwant', help='Checkin to an arbitrary location.')
async def iwant(ctx, *searchstring):
    mystr = ' '.join(searchstring)
    
    query = urllib.parse.quote_plus(mystr)
    print(query)

    r = requests.get('https://tabletop.events/api/library/0AEB11DA-2B7D-11EC-B400-855F800FD618/librarygames?query=' + query)

    results = r.json()
    #import pdb; pdb.set_trace()

    if len(results['result']['items']) > 1:
        msg = "Too many results. Be more specific."
        await ctx.send(msg)
        for result in results['result']['items']:
            msg = result['name']
            await ctx.send(msg)
    elif len(results['result']['items']) == 1:
        if MOCK_CHECKOUT == True:
          results['result']['items'][0]['is_checked_out'] = 1
        msg = "Found the game you were looking for!"
        if results['result']['items'][0]['is_checked_out'] == 1:
            msg = "Oh no! The game is checked out! I will notify you when it is available!"
            trackGame(results['result']['items'][0]['id'], ctx.author.global_name, results['result']['items'][0]['name'])
        else:
            msg = "The game is in the library. Go Go Go Go!"
        await ctx.send(msg)
    else:
        msg = "Nothing found"
        await ctx.send(msg)

    #import pdb; pdb.set_trace()
    

bot.run(TOKEN)