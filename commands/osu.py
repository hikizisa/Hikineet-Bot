import os
import nextcord
from nextcord.ext import commands
from datetime import date, datetime, time, timedelta, timezone
import urllib.parse
import requests


'''
@bot.command(name='tp')
async def timing_point(ctx):
    embed = nextcord.Embed(title='Timing Point',
        url='osu://edit/00:00:000',
        description='00:00:000')
    await ctx.send(embed = embed)
'''


OSUAPI = os.getenv('OSU_TOKEN')
FORUMSID = os.getenv('FORUM_PM_SID')
LOCALCHECK = os.getenv('LOCAL_USER_CHECK')


def osu_api_formatter(args):
    data = 'k' + '=' + OSUAPI + '&'
    for arg in args:
        data += arg[0]
        data += '='
        data += arg[1]
        data += '&'
    data = data[:-1]

    return data
    

#duplicate with one in main
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
        

class Osu(commands.Cog):
    def __init__(self, bot, cursor):
        self.bot = bot
        self.cursor = cursor


    @commands.group()
    async def osu(self, ctx):
        if ctx.invoked_subcommand is None:
            help = 'osu link : osu! 계정을 discord 계정과 연결합니다.\n'
            help += 'osu who : 해당 유저의 osu! 정보를 표시합니다.\n'
            help += 'osu nr : 최신 랭크맵 목록을 보여줍니다.'
            await ctx.send(help)
            
    @osu.command(name='mirror')
    async def mirror_osu(self, ctx, *args):
        pass

    @osu.command(name='who')
    async def who_osu(self, ctx, *args):
        cursor = self.cursor
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

        embed = nextcord.Embed(title=record[0][1], url='https://osu.ppy.sh/users/' + str(record[0][0]),
            description=record[0][0], color=0xecce8b)
        embed.set_image(url = 'https://a.ppy.sh/' + str(record[0][0]) + '_.jpeg')

        await ctx.send(embed = embed)


    @osu.command(name='link')
    async def link_osu(self, ctx, *args):
        cursor = self.cursor
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
    async def new_ranked_map(self, ctx, hrs = None):
        cursor = self.cursor
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

             embed = nextcord.Embed(title = title,
                 url = 'https://osu.ppy.sh/s/' + beatmap['beatmapset_id'],
                 description = beatmap['approved_date'] + '\n' + 'Mapset by ' + beatmap['creator'] + '\n',
                 color = 0xecce8b,
             )
             embed.set_thumbnail(url = 'https://b.ppy.sh/thumb/' + beatmap['beatmapset_id'] + 'l.jpg')

             await ctx.send(embed = embed)