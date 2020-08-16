# bot.py
import signal, sys,os
import sqlite3
import random, string
from datetime import date, datetime, time, timedelta, timezone
import urllib.parse

import requests

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
OSUAPI = os.getenv('OSU_TOKEN')
DBPATH = os.getenv('DB_PATH')
FORUMSID = os.getenv('FORUM_PM_SID')
LOCALCHECK = os.getenv('LOCAL_USER_CHECK')

gacha_colors = (0xc0c0c0, 0xffd700, 0xf0ffff)
priconne_chars = [[], [], []]

with open("priconne.txt", 'r', encoding="utf-8") as f:
    for _, line in enumerate(f):
        parsed = line.split(',')
        if len(parsed) < 3:
            continue
        priconne_chars[int(parsed[2][0])-1].append([parsed[0], parsed[1]])

def interrupt_handler(sig, frame):
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
	
def get_prefix(bot, message):
    prefixes = ['!']

    # Check to see if we are outside of a guild. e.g DM's etc.
    if not message.guild:
        # Only allow ? to be used in DMs
        return '?'

    # If we are in a guild, we allow for the user to mention us or use any of the prefixes in our list.
    return commands.when_mentioned_or(*prefixes)(bot, message)

bot = commands.Bot(command_prefix=get_prefix, description='HikiNeet bot for coding practice', case_insensitive=True)
#bot.add_cog(Osu(bot))

def isInt(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False


@bot.event
async def on_ready():
    print(f'\nLogged in as: {bot.user.name} - {bot.user.id}\nVersion: {discord.__version__}\n')
    print(f'{bot.user} is connected to the following guild:\n')

    for guild in bot.guilds:
        print(
            f'{guild.name}(id: {guild.id})'
        )
    activity=discord.Activity(type=discord.ActivityType.watching, name="cute Yue chan")

    await bot.change_presence(activity=activity)


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
    if not (isInt(max) and isInt(count)):
        await ctx.send('숫자를 입력해주세요.')
        return
    if max > 1000000000 or max < 1:
        await ctx.send('입력 숫자가 범위를 이탈했습니다.')
        return
    if count > 20 or count < 1:
        await ctx.send('주사위의 수가 범위를 이탈했습니다.')
        return

    rng = ''
    for i in range(count):
        num = random.randint(1, int(max))
        rng += str(num) + ' '
    await ctx.send(rng)


@bot.command(aliases=['vs'])
async def choose(ctx, *args):
    str = ' '.join(args)
    rng_array = list(filter(lambda x: x != '', str.split('|')))
    if len(rng_array) <= 1:
        await ctx.send('둘 이상의 선택지를 |로 구분해서 입력해주세요.')
        return
    await ctx.send(random.choice(rng_array))
	

@bot.command(name='gacha')
async def gacha(ctx, ren = 10):
    limit = 10

    if ren > limit or ren < 1:
        await ctx.send(str(limit) + '연차 이내만 가능합니다.')
        return

    pickup = []
    rainbow = []
    gold = []
    silver = []

    prob_pickup = 0.7
    prob_rainbow = 1.8
    prob_gold = 18

    #pickup_emoji = '<:3pickup:665379328976224267>'
    #rainbow_emoji = '<:3sung:665296979420512299>'
    #silver_emoji = '<:sra:635880906242129970>'
    #gold_emoji = '<:sra1:635881449853288449>'

    result = []

    for i in range(ren):
        value = random.random() * 100

        value -= prob_pickup
        if value < 0:
            result.append(random.choice(priconne_chars[2]) + [2])
            continue

        value -= prob_rainbow
        if value < 0:
            result.append(random.choice(priconne_chars[2]) + [2])
            continue

        value -= prob_gold
        if value < 0 or i % 10 == 9:
            result.append(random.choice(priconne_chars[1]) + [1])
            continue

        result.append(random.choice(priconne_chars[0]) + [0])
        
    for char in result:
        embed = discord.Embed(title=char[0] , color=gacha_colors[char[2]])
        embed.set_image(url = char[1])
        await ctx.send(embed = embed)


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


def get_userid(args, ctx):
    if len(args) == 0:
        # defaults to message author
        return ctx.author.id

    name = ' '.join(args)

    # by mention
    if name[0:3] == '<@!' and name[-1] == '>':
        try:
            userid = int(name[3:-1])
            return userid
        except:
            pass

    member = ctx.guild.get_member_named(name)

    if member is not None:
        return member.id


@bot.command(name='pfp')
async def profile_pic(ctx, *args):
    userid = get_userid(args, ctx)

    if userid is None:
        await ctx.send('유저의 이름의 형식이 잘못되었습니다.')
        return

    user = ctx.guild.get_member(userid)
    if not user:
        await ctx.send('유저를 찾을 수 없습니다.')
        return
    '''.format(user.mention)'''

    pfp = user.avatar_url

    embed = discord.Embed(title=user.display_name, description=user.name+'#'+user.discriminator , color=0xecce8b)
    embed.set_image(url = (pfp))

    await ctx.send(embed = embed)
	

@bot.group()
async def osu(ctx):
    if ctx.invoked_subcommand is None:
        help = '!osu link : osu! 계정을 discord 계정과 연결합니다.\n'
        help += '!osu who : 해당 유저의 osu! 정보를 표시합니다.\n'
        help += '!osu nr : 최신 랭크맵 목록을 보여줍니다.'
        await ctx.send(help)


@osu.command(name='who')
async def who_osu(ctx, *args):
    userid = get_userid(args, ctx)

    if userid is None:
        await ctx.send('유저의 이름의 형식이 잘못되었습니다.')
        return

    selectQuery = "SELECT osu_id, osu_name FROM OsuUserName where discord_id = ?;"
    cursor.execute(selectQuery, (str(userid),))
    record = cursor.fetchall()
	
    if len(record) == 0:
        await ctx.send('먼저 osu! 계정을 등록해주세요.')
        return

    embed = discord.Embed(title=record[0][1], url='https://osu.ppy.sh/users/' + str(record[0][0]),
        description=record[0][0], color=0xecce8b)
    embed.set_image(url = 'https://a.ppy.sh/' + str(record[0][0]) + '_.jpeg')

    await ctx.send(embed = embed)


@osu.command(name='link')
async def link_osu(ctx, *args):
    if len(args) == 0:
        await ctx.send('osu! 닉네임이나 ID를 입력해주세요')
        return

    userid = ctx.author.id

    api_args = [('u', ' '.join(args))]
    url = 'https://osu.ppy.sh/api/get_user?' + osu_api_formatter(api_args)

    try:
        response = requests.get(url)
    except requests.exceptions.HTTPError as http_err:
        await ctx.send('API 요청에 실패했습니다.')
        print(f'HTTP error occurred: {http_err}')

    user_data = response.json()
	
    if len(user_data) == 0:
        await ctx.send('해당하는 osu! 계정을 발견하지 못했습니다.')
        return

    osu_name = user_data[0]['username']
    osu_id = user_data[0]['user_id']

    selectQuery = "SELECT osu_id, osu_name FROM OsuUserName where discord_id = ?"
    cursor.execute(selectQuery, (str(userid),))
    record = cursor.fetchall()
	
    if len(record) == 0:
        query = "INSERT INTO OsuUserName (osu_id, osu_name, discord_id) VALUES (?, ?, ?)"
    else:
        query = "UPDATE OsuUserName SET osu_id = ?, osu_name = ? WHERE discord_id = ?"

    cursor.execute(query, (osu_id, osu_name, userid))
	
    await ctx.send('osu! 계정이 설정되었습니다. : ' + osu_name)


@osu.command(name='nr')
async def new_ranked_map(ctx, hrs = None):
    sqlTimeFormat = '%Y-%m-%d %H:%M:%S'
    tz = timezone(timedelta(hours=0))
    now = datetime.now(tz = tz)

    if hrs is None:
        selectQuery = "SELECT * FROM LastUpdate;"
        cursor.execute(selectQuery)
        record = cursor.fetchall()

        sqltime = record[0][0]
        time = datetime.strptime(sqltime, sqlTimeFormat).replace(tzinfo=tz)
		
        currSqlTime = now.strftime(sqlTimeFormat)
        updateQuery = "UPDATE LastUpdate SET time='" + currSqlTime + "';"
        cursor.execute(updateQuery)
		
        hours = int((now - time).total_seconds() / 3600.0)

    else:
        try:
            hours = int(hrs)
        except:
            await ctx.send('정수를 입력해주세요.')
            return

        if hours > 200:
            hours = 200
        if hours < 0:
            hours = 24
        time = now - timedelta(hours=hours)

    sql_time = time.strftime(sqlTimeFormat)
    api_args = [('since', sql_time), ('limit', '500')]

    url = 'https://osu.ppy.sh/api/get_beatmaps?' + osu_api_formatter(api_args)

    try:
        response = requests.get(url)
    except requests.exceptions.HTTPError as http_err:
        await ctx.send('API 요청에 실패했습니다.')
        print(f'HTTP error occurred: {http_err}')

    map_data = response.json()

    str = f'최근 {hours}시간 동안 랭크 된 맵:\n'
    map_titles = []

    if len(map_data) == 0:
        if hrs is None:
            await ctx.send('마지막 확인 이후 랭크된 맵이 없습니다.')
        else:
            await ctx.send(hrs + '시간 동안 랭크된 맵이 없습니다.')
        return
	
    for beatmap in map_data:
         if len(str) >= 2000:
             str = str[0:2000]
             break
         title = beatmap['title']
         if beatmap['approved'] != '1' or title in map_titles:
             continue
         map_titles.append(title)

         embed = discord.Embed(title = title,
             url = 'https://osu.ppy.sh/s/' + beatmap['beatmapset_id'],
             description = beatmap['approved_date'] + '\n' + 'Mapset by ' + beatmap['creator'] + '\n',
             color = 0xecce8b,
         )
         embed.set_thumbnail(url = 'https://b.ppy.sh/thumb/' + beatmap['beatmapset_id'] + 'l.jpg')

         await ctx.send(embed = embed)


bot.run(TOKEN)
