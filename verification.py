# osu account verification
# using old forum pm

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


def osu_api_formatter(args):
    str = 'k' + '=' + OSUAPI + '&'
    for arg in args:
        str += arg[0]
        str += '='
        str += arg[1]
        str += '&'
    str = str[:-1]

    return str


def verify_osu_db(discord_id, osu_id, osu_name):
    selectQuery = "SELECT osu_id, osu_name FROM OsuUserName where discord_id = ?;"
    cursor.execute(selectQuery, (str(discord_id),))
    record = cursor.fetchall()
	
    if len(record) == 0:
        query = "INSERT INTO OsuUserName (osu_id, osu_name, discord_id) VALUES (?, ?, ?);"
    else:
        query = "UPDATE OsuUserName SET osu_id = ?, osu_name = ? WHERE discord_id = ?;"

    cursor.execute(query, (osu_id, osu_name, discord_id))


@bot.command(pass_context = True , aliases=['osur'])
async def register_osu(ctx, *args):
    if len(args) == 0:
        await ctx.send('osu! 닉네임이나 ID를 입력해주세요')
        return

    userid = ctx.author.id

	# find osu! account
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

    # verify only korean users
    if user_data[0]['country'] != 'KR':
        verify_osu_db(userid, osu_id, osu_name)
        await ctx.send('osu! 계정이 설정되었습니다 : ' + osu_name)
        return

    # send verification pm

    # check if user sent verification pm within last 1 hour
    query = "SELECT osu_id, verification_code, time FROM OsuVerification WHERE discord_id = ?;"
    cursor.execute(query, (userid,))
	
    record = cursor.fetchall()

    sqlTimeFormat = '%Y-%m-%d %H:%M:%S'
    tz = timezone(timedelta(hours=0))
    now = datetime.now(tz = tz)

    if len(record) != 0:
        last = datetime.strptime(record[0][2], sqlTimeFormat).replace(tzinfo=tz)
		
        if (now - last).total_seconds() <= 3600.0:
            await ctx.send('1시간 이내에 요청한 인증코드가 대기중입니다.')
            return

        else:
            query = "DELETE FROM OsuVerification WHERE discord_id = ?;"
            cursor.execute(query, (userid,))

    # actually send verification pm
    def randomString(stringLength = 10):
        letters = string.ascii_letters
        return ''.join(random.choice(letters) for i in range(stringLength))

    ver_code = randomString(16)

    pm_body = ("HikiNeet Bot 인증코드입니다.\n[quote]!osuv " + ver_code + "[/quote]\n" +
        "커맨드를 봇 채널에 입력해주세요.\n\n" +
        "이 인증코드는 디스코드 " + ctx.author.name + "#" + ctx.author.discriminator + "님에 의해 요청되었습니다.\n"
        "본인이 인증코드를 요청하지 않았다면, 이 PM을 무시하거나 답장으로 문의해주세요.")

    url = "https://old.ppy.sh/forum/ucp.php?i=pm&mode=compose&action=post&sid=" + FORUMSID
    data = {"username_list": '', "localUserCheck": LOCALCHECK, "address_list[u][" + str(user_data[0]['user_id']) + "]": 'to',
        "subject": "Hikineet Bot 인증 PM", "icon": 0, "addbbcode20": 100, "message": pm_body, "preview": '', "post": '1', "save": '', "load": '', "cancel": '',}
    try:
        response = requests.post(url, data)
    except requests.exceptions.HTTPError as http_err:
        await ctx.send('API 요청에 실패했습니다.')
        print(f'HTTP error occurred: {http_err}')
		
    currSqlTime = now.strftime(sqlTimeFormat)
    query = "INSERT INTO OsuVerification (discord_id, osu_id, osu_name, verification_code, time) VALUES (?, ?, ?, ?, ?);"
    cursor.execute(query, (userid, osu_id, osu_name, ver_code, currSqlTime))

    await ctx.send('한국 osu! 유저는 포럼PM을 통한 인증이 필요합니다.')
    await ctx.send('해당 osu! 계정에 인증번호 PM을 전송했습니다. !osuv로 계정 연동을 완료해주세요.')

	
@bot.command(pass_context = True , aliases=['osuv'])
async def verify_osu(ctx, code = ''):
    userid = ctx.author.id
    query = "SELECT osu_id, osu_name, verification_code, time FROM OsuVerification WHERE discord_id = ?;"
    cursor.execute(query, (userid,))
	
    record = cursor.fetchall()
	
    if len(record) == 0:
        await ctx.send('요청한 인증번호가 없습니다.')
        return

    sqlTimeFormat = '%Y-%m-%d %H:%M:%S'
    tz = timezone(timedelta(hours=0))

    now = datetime.now(tz = tz)
    last = datetime.strptime(record[0][3], sqlTimeFormat).replace(tzinfo=tz)
		
    if (now - last).total_seconds() > 3600.0:
        await ctx.send('인증코드가 만료되었습니다. 다시 인증해주세요.')
        query = "DELETE FROM OsuVerification WHERE discord_id = ?;"
        cursor.execute(query, (userid,))
        return
    
    if code == record[0][2]:
        osu_id = record[0][0]
        osu_name = record[0][1]
        verify_osu_db(userid, osu_id, osu_name)

        query = "DELETE FROM OsuVerification WHERE discord_id = ?;"
        cursor.execute(query, (userid,))

        await ctx.send('osu! 계정이 설정되었습니다 : ' + osu_name)

    else:
        await ctx.send('인증코드가 잘못되었습니다.')


bot.run(TOKEN)
