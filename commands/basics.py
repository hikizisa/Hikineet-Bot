# game_over / pass -> one function
# sql to separate function
# play command : retry on error

import os
import discord
from discord.ext import commands
import random, string

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

    def shutdown_bot(self):
        if (self.sqliteConnection):
            self.sqliteConnection.commit()
            self.sqliteConnection.close()

        os._exit(0)

    @commands.command(name='shutdown')
    async def shutdown(self, ctx):
        if ctx.author.id == int(self.HOST):
            await ctx.send("봇을 종료합니다.")
            self.shutdown_bot()
        else:
            await ctx.send("권한이 없습니다.")

    @commands.command(name='say')
    async def say(self, ctx, *args):
        if ctx.author.id == int(self.HOST):
            msg = " ".join(args)
            await ctx.send(msg)
        else:
            await ctx.send("권한이 없습니다.")

    @commands.Cog.listener()
    async def on_ready(self):
        activity=discord.Activity(type=discord.ActivityType.watching, name="dmld")

        await self.bot.change_presence(activity=activity)

    '''
    @commands.Cog.listener()
    async def on_member_join(member):
        await member.create_dm()
        await member.dm_channel.send(
            f'Hi {member.name}, welcome to my Discord server!'
        )
    '''

    async def copypasta(self, message):
    # gonna do something with https://pypi.org/project/python-sql/ later
        repl = False
        cid = message.channel.id
        if (cid in self.last_msg and self.last_msg[cid].content == message.content and
            not (cid in self.llast_msg and self.llast_msg[cid].content == message.content) and
            not self.last_msg[cid].author.id == message.author.id and
            not self.last_msg[cid].author.bot):
            repl = True
        
        if cid in self.last_msg:
            self.llast_msg[cid] = self.last_msg[cid]
        self.last_msg[cid] = message
        
        if repl and len(message.content) > 0:
            await message.channel.send(message.content)


    async def on_message(self, message):
        await self.copypasta(message)
        
        if message.author.bot:
            return
            
        if ' ' not in message.content:
            compo = message.content.split('/')
            if len(compo) >= 5:
                if compo[2] == "discord.com" and compo[3] == "channels":
                    try:
                        chn = self.bot.get_channel(int(compo[-2]))
                        server = self.bot.get_guild(int(compo[-3]))
                        msg = await chn.fetch_message(int(compo[-1]))
                    
                        embed = discord.Embed(title = '%s - %s' % (server.name, chn.name),
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

        embed = discord.Embed(title=user.display_name, description=user.name+'#'+user.discriminator , color=0xecce8b)
        embed.set_image(url = (pfp))

        await ctx.send(embed = embed)
