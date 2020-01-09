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


def isInt(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False


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


@bot.command(pass_context = True , aliases=['vs'])
async def choose(ctx, *args):
    str = ' '.join(args)
    rng_array = list(filter(lambda x: x != '', str.split('|')))
    if len(rng_array) <= 1:
        await ctx.send('둘 이상의 선택지를 |로 구분해서 입력해주세요.')
        return
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


@bot.command(pass_context = True , aliases=['getosu'])
async def get_osu_name(ctx, *args):
    userid = get_userid(args, ctx)

    if userid is None:
        await ctx.send('유저의 이름의 형식이 잘못되었습니다.')
        return

    selectQuery = "SELECT osu_id, osu_name FROM OsuUserName where discord_id = ?"
    cursor.execute(selectQuery, (str(userid),))
    record = cursor.fetchall()
	
    if len(record) == 0:
        await ctx.send('먼저 osu! 계정을 등록해주세요.')
        return

    embed = discord.Embed(title=record[0][1], url='https://osu.ppy.sh/users/' + str(record[0][0]),
        description=record[0][0], color=0xecce8b)
    embed.set_image(url = 'https://a.ppy.sh/' + str(record[0][0]) + '_.jpeg')

    await ctx.send(embed = embed)


@bot.command(pass_context = True , aliases=['setosu'])
async def set_osu_name(ctx, *args):
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

    selectQuery = "INSERT INTO OsuUserName (discord_id, osu_id, osu_name) VALUES (?, ?, ?)"
    cursor.execute(selectQuery, (userid, osu_id, osu_name))
    record = cursor.fetchall()
	
    await ctx.send('osu! 계정이 설정되었습니다. : ' + osu_name)


@bot.command(name='nr')
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
