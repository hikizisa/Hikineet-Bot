# bot.py
import signal, sys, os
import sqlite3
import random, string

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
DBPATH = os.getenv('DB_PATH')
HOST = os.getenv('HOST')

from commands.priconne import Priconne
from commands.osu import Osu


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


def shutdown_bot():
    if (sqliteConnection):
        sqliteConnection.commit()
        sqliteConnection.close()
        print("The SQLite connection is closed")

    print("Shutting down bot")
    sys.exit(0)
    

@bot.command(name='shutdown')
async def shutdown(ctx):
    print(ctx.author.id, HOST)
    if ctx.author.id == int(HOST):
        await ctx.send("봇을 종료합니다.")
        shutdown_bot()
    else:
        await ctx.send("권한이 없습니다.")


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
	

bot.add_cog(Priconne(bot))
bot.add_cog(Osu(bot, cursor))
bot.run(TOKEN)
