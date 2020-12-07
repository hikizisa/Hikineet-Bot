import os
import discord
from discord.ext import commands
import time as timer
from datetime import date, datetime, time, timedelta, timezone
import urllib.parse
import requests
from io import BytesIO
from pydub import AudioSegment
from threading import Timer

class Omq(commands.Cog):
    def __init__(self, bot, cursor):
        self.bot = bot
        self.cursor = cursor
        self.round_id = 0
        
        omq_song_dir = "./tmp/audios/omq/"
        if not os.path.exists(omq_song_dir):
            os.makedirs(omq_song_dir)
        
        queries = []
        queries.append("DROP TABLE IF EXISTS OmqRound;")
        queries.append("CREATE TABLE IF NOT EXISTS OmqRound (channel_id INT, round_id INT, song_name STRING);")
    
        for query in queries:
            cursor.execute(query)

    @commands.group()
    async def omq(self, ctx):
        if ctx.invoked_subcommand is None:
            help = '!omq add (mapsetID) [songName] : 퀴즈 대상 곡을 추가합니다.\n'
            help += '!omq length (sec) : 재생할 프리뷰의 길이를 지정합니다.\n'
            help += '!omq timeout [sec] : 정답을 받을 시간을 지정합니다. 시간을 지정하지 않으면 무제한이 됩니다.\n'
            help += '!omq setting : 현재 서버의 세팅을 확인합니다.\n'
            help += '!omq play : 퀴즈를 플레이합니다.\n'
            help += '!omq answer (songName) : 퀴즈의 답변을 제시합니다. 대소문자와 띄어쓰기는 무시합니다.\n'
            help += '!omq list : 퀴즈 대상 곡의 목록을 보여줍니다.\n'
            help += '!omq remove (id) : 지정한 곡을 퀴즈 목록에서 제거합니다.\n'
            help += '!omq terminate : 퀴즈를 강제로 종료합니다.'
            await ctx.send(help)

    @omq.command(name='add')
    async def add_song(self, ctx, *args):
        cursor = self.cursor
        
        guild = ctx.guild.id
        if len(args) < 2:
            ctx.send('곡 ID와 곡명을 입력해주세요.')
            return
            
        song_id = args[0]
        song_name = ' '.join(args[1:])
        
        omq_song_dir = "./tmp/audios/omq/"
        
        mp3 = requests.get('https://b.ppy.sh/preview/' + song_id + '.mp3')
        with open(omq_song_dir + song_id + '.mp3', 'wb') as f:
            f.write(mp3.content)

        insertQuery = "INSERT into OsuQuiz (server_id, mapset_id, song_name) VALUES (?, ?, ?);"
        cursor.execute(insertQuery, (guild, song_id, song_name))
        record = cursor.fetchall()

        await ctx.send(song_id + " - " + song_name + "가 추가되었습니다.")
        
    @omq.command(name='length')
    async def set_length(self, ctx, *args):
        cursor = self.cursor
        length = None
        
        try:
            length = int(args[0])
        except:
            await ctx.send("ms 단위의 정수로 프리뷰 길이를 지정해주세요!")
            return
            
        if length < 100 or length > 10000:
            await ctx.send("100 ~ 10000ms로만 지정할 수 있습니다!")
            return

        guild_id = ctx.guild.id
        
        checkQuery = "SELECT * from OsuQuizSettings where server_id = ?;"
        cursor.execute(checkQuery, (guild_id,))
        record = cursor.fetchall()
        
        if len(record) == 0:
            createQuery = "INSERT into OsuQuizSettings VALUES (?, ?, 60);"
            cursor.execute(createQuery, (guild_id, length))
        else:
            updateQuery = "UPDATE OsuQuizSettings SET length = ? WHERE server_id = ?;"
            cursor.execute(updateQuery, (length, guild_id))
        await ctx.send("프리뷰 길이를 " + str(length) + "초로 설정했습니다!")
        
    @omq.command(name='timeout')
    async def set_timeout(self, ctx, *args):
        cursor = self.cursor
        timeout = None
        
        try:
            timeout = int(args[0])
        except:
            await ctx.send("초 단위의 정수로 시간을 지정해주세요!")
            return
            
        if timeout < 10 or timeout > 120:
            await ctx.send("10 ~ 120초로만 지정할 수 있습니다!")
            return

        guild_id = ctx.guild.id
        
        checkQuery = "SELECT * from OsuQuizSettings where server_id = ?;"
        cursor.execute(checkQuery, (guild_id,))
        record = cursor.fetchall()
        
        if len(record) == 0:
            createQuery = "INSERT into OsuQuizSettings VALUES (?, 1, ?);"
            cursor.execute(createQuery, (guild_id, timeout))
        else:
            updateQuery = "UPDATE OsuQuizSettings SET timeout = ? WHERE server_id = ?;"
            cursor.execute(updateQuery, (timeout, guild_id))
        await ctx.send("제한 시간을 " + str(timeout) + "초로 설정했습니다!")
        
    async def game_over(self, round_id):
        cursor = self.cursor
        checkQuery = "SELECT * from OmqRound where round_id = ?;"
        cursor.execute(checkQuery, (round_id,))
        record = cursor.fetchall()
        
        if len(record) == 0:
            return
            
        channel = self.bot.get_channel(record[0][0])
        await channel.send("시간이 초과되었습니다.")
        await channel.send("정답은 " + record[0][2] + "입니다!")
        
        # remove quiz from database
        removeQuery = "DELETE from OmqRound where round_id = ?;"
        cursor.execute(removeQuery, (round_id,))
        
    @omq.command(name='play')
    async def play(self, ctx, *args):
        self.round_id += 1
        cursor = self.cursor
        
        checkQuery = "SELECT * from OmqRound where channel_id = ?;"
        cursor.execute(checkQuery, (ctx.channel.id,))
        record = cursor.fetchall()
        if len(record) > 0:
            await ctx.send("이미 라운드가 진행중입니다!")
            return
        
        # Retrieve quiz settings and songs in the server
        guild_id = ctx.guild.id
        selectQuery = "SELECT * from OsuQuiz where server_id = ? ORDER BY RANDOM() LIMIT 1;"
        cursor.execute(selectQuery, (guild_id,))
        record = cursor.fetchall()
        
        if len(record) == 0:
            await ctx.send("등록된 곡이 없습니다!")
            return

        answer = record[0][2]
        
        # Check server settings
        checkQuery = "SELECT * from OsuQuizSettings where server_id = ?;"
        cursor.execute(checkQuery, (guild_id,))
        settings = cursor.fetchall()
        
        timeout = 60
        length = 1000
        if len(settings) > 0:
            length = settings[0][1]
            timeout = settings[0][2]
        
        # Cut mp3 following server setting
        omq_song = "./tmp/audios/omq/" + str(record[0][1]) + '.mp3'
        omq_song_cut = "./tmp/audios/omq/" + str(record[0][1]) + 'cut.mp3'
        
        sound = AudioSegment.from_mp3(omq_song)
        if len(sound) > length:
            sound = sound[:length]
        sound.export(omq_song_cut, format="mp3")
        
        # Send messages
        await ctx.send("'!omq answer (제목)'으로 곡 제목을 맞춰주세요!")
        mp3 = open(omq_song_cut, 'rb')
        await ctx.send(file=discord.File(fp=mp3, filename="quiz.mp3"))
        
        # Add round to database
        quiz_round_query = "INSERT INTO OmqRound VALUES(?, ?, ?);"
        record = cursor.execute(quiz_round_query, (ctx.channel.id, self.round_id, answer))
        
        timer.sleep(timeout)
        await self.game_over(self.round_id)
        
    @omq.command(name='answer')
    async def answer(self, ctx, *args):
        cursor = self.cursor
        
        # read pending quiz data
        checkQuery = "SELECT * from OmqRound where channel_id = ?;"
        cursor.execute(checkQuery, (ctx.channel.id,))
        record = cursor.fetchall()

        if len(record) == 0:
            await ctx.send("진행중인 라운드가 없습니다!")
            return
        
        if len(args) < 1:
            await ctx.send('곡 제목을 입력해주세요.')
            return
         
        answer = ' '.join(args)
        answer = answer.replace(" ", "").lower()
        true_answer = record[0][2].replace(" ", "").lower()
        
        if answer == true_answer:
            await ctx.send("정답입니다, " + ctx.author.name + "님!")
            # remove quiz from database
            removeQuery = "DELETE from OmqRound where channel_id = ?;"
            cursor.execute(removeQuery, (ctx.channel.id,))
        
    @omq.command(name='setting')
    async def settings(self, ctx, *args):
        cursor = self.cursor
        
        guild_id = ctx.guild.id
        
        checkQuery = "SELECT * from OsuQuizSettings where server_id = ?;"
        cursor.execute(checkQuery, (guild_id,))
        record = cursor.fetchall()
        
        timeout = 60
        length = 1000
        if len(record) > 0:
            length = record[0][1]
            timeout =  record[0][2]
            
        await ctx.send("현재 서버에서 프리뷰 길이는 " + str(length) + "ms이며 " + "제한 시간은 " + str(timeout) + "초입니다.")
        
    @omq.command(name='list')
    async def list(self, ctx, *args):
        pass

    @omq.command(name='remove')
    async def remove_song(self, ctx, *args):
        pass

    @omq.command(name='terminate')
    async def terminate(self, ctx, *args):
        pass