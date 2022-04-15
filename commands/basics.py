import os
import nextcord
from nextcord.ext import commands
import random, string
from time import sleep
import subprocess
import sys
import asyncio

def isInt(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False
            
class Basics(commands.Cog):
    def __init__(self, bot, cursor, sqliteConnection):
        self.bot = bot
        self.cursor = cursor
        self.sqliteConnection = sqliteConnection
        self.llast_msg = {}
        self.last_msg = {}
        self.HOST = os.getenv("HOST")

    def close_sqlite(self):
        if (self.sqliteConnection):
            self.sqliteConnection.commit()
            self.sqliteConnection.close()

    @commands.command(name='shutdown')
    async def shutdown(self, ctx):
        if ctx.author.id == int(self.HOST):
            await ctx.send("봇을 종료합니다.")
            self.close_sqlite()
            os._exit(0)
        else:
            await ctx.send("권한이 없습니다.")

    @commands.command(name='restart')
    async def restart(self, ctx):
        if ctx.author.id == int(self.HOST):
            await ctx.send("봇을 재시작합니다.")
            self.close_sqlite()
            subprocess.Popen(["python", "main.py"])
            print("")
            os._exit(0)
        else:
            await ctx.send("권한이 없습니다.")

    @commands.command(name='say')
    async def say(self, ctx, *args):
        if ctx.author.id == int(self.HOST):
            msg = " ".join(args)
            try:
                await ctx.message.delete()
            except:
                pass
            await ctx.send(msg)
        else:
            await ctx.send("권한이 없습니다.")
        
    @commands.command(name='mirror')
    async def get_mirror(self, ctx, *args):
        map_id = None
        
        arg = ' '.join(args)
        parsed_arg = arg.split('/')
        if len(parsed_arg) < 4:
            try:
                map_id = int(parsed_arg)
            except:
                return
        elif parsed_arg[2] == 'osu.ppy.sh' and parsed_arg[3] == 'beatmapsets':
            map_id = parsed_arg[4].split('#')[0]
        else:
            return

        url = 'https://api.chimu.moe/v1/download/{}?n=1'.format(map_id)
        embed = nextcord.Embed(title='Chimu Beatmap Mirror', url=url, color=0xecce8b, description='Click for Download')

        await ctx.send(embed = embed)
        
    @commands.command(name='pretend')
    async def pretend(self, ctx, *args):
        if ctx.author.id == int(self.HOST) and len(args) >= 2:
            userid = self.get_userid([args[0]], ctx)
            msg = " ".join(args[1:])
            
            try:
                await ctx.message.delete()
            except:
                pass
            
            member = ctx.guild.get_member(userid)
            if member is None:
                return

            webhook = await ctx.channel.create_webhook(name=member.name)
                
            await webhook.send(
                str(msg), username=member.nick, avatar_url=member.avatar_url)
                
            await webhook.delete()
        else:
            await ctx.send("권한이 없습니다.")
        

    @commands.Cog.listener()
    async def on_ready(self):
        #activity=nextcord.Activity(type=nextcord.ActivityType.watching, name="dmld")

        #await self.bot.change_presence(activity=activity)
        pass

    '''
    @commands.Cog.listener()
    async def on_member_join(member):
        await member.create_dm()
        await member.dm_channel.send(
            f'Hi {member.name}, welcome to my Discord server!'
        )
    '''
    
    async def send_copypasta(self, message):
        sleep(random.uniform(0.0, 1.0))
        await message.channel.send(message.content)

    async def copypasta(self, message):
    # gonna do something with https://pypi.org/project/python-sql/ later
        repl = False
        cid = message.channel.id
        if (cid in self.last_msg and self.last_msg[cid].content == message.content and
            not (cid in self.llast_msg and self.llast_msg[cid].content == message.content) and
            not self.last_msg[cid].author.id == message.author.id):
            repl = True
            
        #if cid in self.last_msg and self.last_msg[cid].content != message.content:
        #    if len(message.content.encode('utf8')) <= 5 and random.randint(0, 100) >= 0:
        #        self.llast_msg[cid].content = message.content
        #        self.last_msg[cid].content = message.content
        #        loop.create_task(self.send_copypasta(message))
        
        if cid in self.last_msg:
            self.llast_msg[cid] = self.last_msg[cid]
        self.last_msg[cid] = message
        
        if repl and len(message.content) > 0:
            loop = asyncio.get_event_loop()
            loop.create_task(self.send_copypasta(message))


    async def on_message(self, message):
        if message.author.bot:
            return
            
        if self.bot.user.mentioned_in(message):
            if not ("@here" in message.content or "@everyone" in message.content):
                await message.reply("안녕하세요! {}님".format(message.author.mention))

        await self.copypasta(message)
            
        if ' ' not in message.content:
            compo = message.content.split('/')
            if len(compo) >= 5:
                if compo[2] == "discord.com" and compo[3] == "channels":
                    chn = None
                    server = None
                    msg = None
                    
                    try:
                        server = self.bot.get_guild(int(compo[-3]))
                    except:
                        return

                    try:
                        chn = self.bot.get_channel(int(compo[-2]))
                        msg = await chn.fetch_message(int(compo[-1]))
                    except:
                        chn = {"name": "알 수 없음"}
                        msg = {"content": "메시지 내용을 알 수 없습니다."}
                    
                    try:
                        embed = nextcord.Embed(title = '%s - %s' % (server.name, chn.name),
                             description = msg.content,
                             color = 0xecce8b,
                        )
                        await message.channel.send(embed = embed)
                    except:
                        pass

        if '오네쨩' == message.content:
            response = '<:emoji_90:660939513299992576>'
            await message.channel.send(response)
            
        if '<a:fastratJAM:811561886188568576>' == message.content:
            response = '<a:WatameBang:812993518686699550>'
            await message.channel.send(response)

    @commands.command(name='roll')
    async def roll(self, ctx, max = 100, count = 1):
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


    @commands.command(aliases=['vs'])
    async def choose(self, ctx, *args):
        str = ' '.join(args)
        rng_array = list(filter(lambda x: x != '', str.split('|')))
        if len(rng_array) <= 1:
            await ctx.send('둘 이상의 선택지를 |로 구분해서 입력해주세요.')
            return
        await ctx.send(random.choice(rng_array))


    def get_userid(self, args, ctx):
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


    @commands.command(name='pfp')
    async def profile_pic(self, ctx, *args):
        userid = self.get_userid(args, ctx)

        if userid is None:
            await ctx.send('유저의 이름의 형식이 잘못되었습니다.')
            return

        user = ctx.guild.get_member(userid)
        
        if not user:
            await ctx.send('유저를 찾을 수 없습니다.')
            return
        '''.format(user.mention)'''

        pfp = user.avatar_url

        embed = nextcord.Embed(title=user.display_name, description=user.name+'#'+user.discriminator , color=0xecce8b)
        embed.set_image(url = (pfp))

        await ctx.send(embed = embed)
