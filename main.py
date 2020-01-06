# bot.py
import signal, sys,os
import sqlite3
import random
from datetime import date, datetime, time, timedelta, timezone

import requests

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
OSUAPI = os.getenv('OSU_TOKEN')
DBPATH = os.getenv('DB_PATH')

def interrupt_handler(sig, frame):
    print("\n")

    if (sqliteConnection):
        sqliteConnection.commit()
        sqliteConnection.close()
        print("The SQLite connection is closed")

    print("Shutting down bot")
    sys.exit(0)

signal.signal(signal.SIGINT, interrupt_handler)

try:
    sqliteConnection = sqlite3.connect(DBPATH)
    cursor = sqliteConnection.cursor()
    print("Successfully Connected to SQLite")

    sqlite_select_Query = "select sqlite_version();"
    cursor.execute(sqlite_select_Query)
    record = cursor.fetchall()
    print("SQLite Database Version is: ", record)

except sqlite3.Error as error:
    print("Error while connecting to sqlite", error)
    sys.exit(0)

bot = commands.Bot(command_prefix='!')

@bot.event
async def on_ready():
    print(f'{bot.user} is connected to the following guild:\n')
    for guild in bot.guilds:
        print(
            f'{guild.name}(id: {guild.id})'
        )

'''
@bot.event
async def on_member_join(member):
    await member.create_dm()
    await member.dm_channel.send(
        f'Hi {member.name}, welcome to my Discord server!'
    )
'''

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if '오네쨩' == message.content:
        response = '<:emoji_90:660939513299992576>'
        await message.channel.send(response)
		
    if '유니콘은' == message.content:
        response = '살아있어'
        await message.channel.send(response)

    if '이의있소' == message.content:
        response = '<:8_:625386426447429643><:7_:625386445372260353>'
        await message.channel.send(response)

    await bot.process_commands(message)

@bot.command(name='roll')
async def roll(ctx, max = 100, count = 1):
    if max > 1000000000:
        await ctx.send('너무 큰 수를 입력했습니다.')
        return
    if count > 20:
        await ctx.send('주사위의 수가 너무 많습니다.')
        return

    rng = ''
    for i in range(count):
        num = random.randint(1, int(max))
        rng += str(num) + ' '
    await ctx.send(rng)

@bot.command(pass_context = True , aliases=['vs'])
async def choose(ctx, *args):
    str = ' '.join(args)
    rng_array = str.split('|')
    await ctx.send(random.choice(rng_array))

'''
@bot.command(name='tp')
async def timing_point(ctx):
    embed = discord.Embed(title='Timing Point',
        url='osu://edit/00:00:000',
        description='00:00:000')
    await ctx.send(embed = embed)
'''

def osu_api_formatter(args):
    str = 'k' + '=' + OSUAPI + '&'
    for arg in args:
        str += arg[0]
        str += '='
        str += arg[1]
        str += '&'
    str = str[:-1]

    return str

@bot.command(name='nr')
async def new_ranked_map(ctx, hrs = None):
    sqlTimeFormat = '%Y-%m-%d %H:%M:%S'
    tz = timezone(timedelta(hours=0))
    now = datetime.now(tz = tz)

    if hrs == None:
        selectQuery = "SELECT * FROM LastUpdate;"
        cursor.execute(selectQuery)
        record = cursor.fetchall()

        sqltime = record[0][0]
        time = datetime.strptime(sqltime, sqlTimeFormat)
		
        currSqlTime = now.strftime(sqlTimeFormat)
        updateQuery = "UPDATE LastUpdate SET time='" + currSqlTime + "';"
        cursor.execute(updateQuery)

    else:
        try:
            hours = int(hrs)
        except:
            await ctx.send('숫자를 입력해주세요.')
            return

        if hours > 7 * 24:
            hours = 7 * 24
        time = now - timedelta(hours=hours)

    sql_time = time.strftime(sqlTimeFormat)
    args = [('since', sql_time), ('limit', '500')]

    url = 'https://osu.ppy.sh/api/get_beatmaps?' + osu_api_formatter(args)
    response = requests.get(url)
    map_data = response.json()

    str = ''
    map_titles = []

    for beatmap in map_data:
         title = beatmap['title']
         if beatmap['approved'] != '1' or title in map_titles:
             continue
         map_titles.append(title)
         url = 'https://osu.ppy.sh/s/' + beatmap['beatmapset_id']
         str += beatmap['approved_date'] + ': ' + title + ' <' + url + '>' + '\n'

    if str != '':
        await ctx.send(str)
    else:
        if hrs == None:
            await ctx.send('마지막 확인 이후 랭크된 맵이 없습니다.')
        else:
            await ctx.send(hrs + '시간 동안 랭크된 맵이 없습니다.')

bot.run(TOKEN)