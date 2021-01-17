# game_over / pass -> one function
# sql to separate function
# play command : retry on error

import os
import discord
from discord.ext import commands
import time as timer
from datetime import date, datetime, time, timedelta, timezone
import urllib.parse
from urllib.error import URLError, HTTPError
import requests
import urllib.request as request
import asyncio
from io import BytesIO
from pydub import AudioSegment
from threading import Timer


class Omq(commands.Cog):
    def __init__(self, bot, cursor):
        self.bot = bot
        self.round_id = 0
        
        self.cursor = cursor
        
        omq_song_dir = "./tmp/audios/omq/"
        if not os.path.exists(omq_song_dir):
            os.makedirs(omq_song_dir)
            
        omq_txt_dir = "./tmp/texts/omq"
        if not os.path.exists(omq_txt_dir):
            os.makedirs(omq_txt_dir)
        
        queries = []
        queries.append("DROP TABLE IF EXISTS OmqRoundAnswer;")
        queries.append("CREATE TABLE IF NOT EXISTS OmqRoundAnswer (channel_id INT, round_id INT, song_name STRING);")
        queries.append("DROP TABLE IF EXISTS OmqRoundScore;")
        queries.append("CREATE TABLE IF NOT EXISTS OmqRoundScore (channel_id INT, user_id STRING, score INT);")
        queries.append("DROP TABLE IF EXISTS OmqRound;")
        queries.append("CREATE TABLE IF NOT EXISTS OmqRound (channel_id INT);")
    
        for query in queries:
            cursor.execute(query)


    @commands.group()
    async def omq(self, ctx):
        if ctx.invoked_subcommand is None:
            help = "`omq add (mapsetID) [songName] : 퀴즈 대상 곡을 추가합니다.\n"
            help += "omq length (ms) : 재생할 프리뷰의 길이를 지정합니다.\n"
            help += "omq timeout [sec] : 정답을 받을 시간을 지정합니다. 시간을 지정하지 않으면 무제한이 됩니다.\n"
            help += "omq setting : 현재 서버의 세팅을 확인합니다.\n"
            help += "omq play : 퀴즈를 플레이합니다.\n"
            help += "omq answer (songName) : 퀴즈의 답변을 제시합니다. 대소문자와 띄어쓰기는 무시합니다.\n"
            help += "omq list [offset] [limit] : 퀴즈 대상 곡의 목록을 보여줍니다.\n"
            help += "omq remove (mapsetID) : 지정한 곡을 퀴즈 목록에서 제거합니다.\n"
            help += "omq reset : 서버에 지정 곡 목록을 초기화 합니다.\n"
            help += "omq pass : 퀴즈를 강제로 종료합니다.\n"
            help += "omq stop : 라운드를 종료합니다."
            help += "`"
            await ctx.send(help)
            
            
    async def download_song(self, song_id):
        omq_song_dir = "./tmp/audios/omq/"
        if not os.path.isfile(omq_song_dir + str(song_id) + '.mp3'):
            mp3 = requests.get('https://b.ppy.sh/preview/' + str(song_id) + '.mp3')
            with open(omq_song_dir + str(song_id) + '.mp3', 'wb') as f:
                f.write(mp3.content)
            
            
    async def add_song_db(self, separated_line, guild):
        if len(separated_line) == 1:
            #find song title from API request
            return
            
        cursor = self.cursor
        
        song_id = separated_line[0]
        try:
            song_id = int(song_id)
        except:
            return
            
        song_name = ' '.join(separated_line[1:])
        await self.download_song(song_id)
        
        print(guild, song_id, song_name)

        insertQuery = "INSERT into OsuQuiz (server_id, mapset_id, song_name) VALUES (?, ?, ?);"
        cursor.execute(insertQuery, (guild, song_id, song_name))


    @omq.command(name='add')
    async def add_song(self, ctx, *args):
        guild = ctx.guild.id
        if len(args) < 2:
            await self.add_db(ctx, guild, args[0])
            return
            
        await self.add_song_db(args, guild)
        await ctx.send(str(args[0]) + " - " + ' '.join(args[1:]) + "가 추가되었습니다.")
    
    
    async def add_db(self, ctx, guild, url):
        data = None
        try:
            headers = {"User-Agent" : "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.95 Safari/537.11"}
            req = request.Request(url, headers=headers)
            data = request.urlopen(req)
        except HTTPError as e:
            print("URL: " + url + ", Code: " + str(e.getcode()) + ", " + str(e.read()))
            await ctx.send("해당 URL을 열 수 없습니다.")
            return
        except:
            await ctx.send("해당 URL을 열 수 없습니다.")
            return

        for line in data:
            line = line.decode("utf-8").replace("\t", "").rstrip()
            space = line.split(" ")
            
            await self.add_song_db(space, guild)
        
        await ctx.send("곡 목록을 등록했습니다!")
        
        
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
        
    
    @omq.command(name='stop')
    async def stop(self, ctx, *args):
        cursor = self.cursor

        # retrieve quiz from database
        selectQuery = "SELECT * from OmqRoundAnswer where channel_id = ?;"
        cursor.execute(selectQuery, (ctx.channel.id,))
        record = cursor.fetchall()
        
        if len(record) == 0:
            await ctx.send("진행 중인 라운드가 없습니다.")
            return
        else:
            selectQuery = "DELETE from OmqRoundAnswer where channel_id = ?;"
            cursor.execute(selectQuery, (ctx.channel.id,))
            await ctx.send("라운드가 종료되었습니다!")
        
        
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
            createQuery = "INSERT into OsuQuizSettings VALUES (?, 1000, ?);"
            cursor.execute(createQuery, (guild_id, timeout))
        else:
            updateQuery = "UPDATE OsuQuizSettings SET timeout = ? WHERE server_id = ?;"
            cursor.execute(updateQuery, (timeout, guild_id))
        await ctx.send("제한 시간을 " + str(timeout) + "초로 설정했습니다!")
        
        
    async def game_over(self, ctx, timeout, round_id = None):
        await asyncio.sleep(timeout)
        cursor = self.cursor
        channel_id = ctx.channel.id
        
        # retrieve quiz from database
        selectQuery = None
        if round_id is None:
            selectQuery = "SELECT * from OmqRoundAnswer where channel_id = ?;"
            cursor.execute(selectQuery, (channel_id,))
        else:
            selectQuery = "SELECT * from OmqRoundAnswer where round_id = ?;"
            cursor.execute(selectQuery, (round_id,))

        record = cursor.fetchall()
        
        if len(record) == 0:
            if round_id is None:
                await ctx.send("진행 중인 라운드가 없습니다.")
            return
        
        rowcount = 0
        if len(record) > 0:
            if round_id is None:
                selectQuery = "DELETE from OmqRoundAnswer where channel_id = ?;"
                cursor.execute(selectQuery, (channel_id,))
                rowcount = cursor.rowcount
            else:
                selectQuery = "DELETE from OmqRoundAnswer where round_id = ?;"
                cursor.execute(selectQuery, (round_id,))
                rowcount = cursor.rowcount
        
        if rowcount > 0:
            channel = self.bot.get_channel(record[0][0])
            if round_id is None:
                await ctx.send("라운드가 취소되었습니다!")
            else:
                await channel.send("시간이 초과되었습니다.")
            await channel.send("정답은 `" + record[0][1] + "`입니다!")
            
            await self.play(ctx, True)


    @omq.command(name='pass')
    async def pass_round(self, ctx, *args):
        await self.game_over(ctx, 0)


    @omq.command(name='play')
    async def play(self, ctx, auto = False, *args):
        cursor = self.cursor
        
        checkQuery = "SELECT * from OmqRoundAnswer where channel_id = ?;"
        cursor.execute(checkQuery, (ctx.channel.id,))
        record = cursor.fetchall()
        if len(record) > 0:
            if not auto:
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
        
        sound = None
        try:
            sound = AudioSegment.from_mp3(omq_song)
        except:
            await ctx.send("출제 중 오류가 발생했습니다! 다시 시도해주세요.")
            return
            
        if len(sound) > length:
            sound = sound[:length]
        sound.export(omq_song_cut, format="mp3")
        
        if answer.replace(" ", "") == "":
            return
        
        # Add round to database
        quiz_round_query = "INSERT INTO OmqRoundAnswer SELECT ?, ?, ? WHERE NOT EXISTS(SELECT 1 FROM OmqRoundAnswer where channel_id = ?);"
        record = cursor.execute(quiz_round_query, (ctx.channel.id, answer, self.round_id, ctx.channel.id))
        self.round_id += 1
        
        if cursor.rowcount >= 1:
            # Send messages
            await ctx.send("곡 제목을 맞춰주세요!")
            mp3 = open(omq_song_cut, 'rb') 
            await ctx.send(file=discord.File(fp=mp3, filename="quiz.mp3"))
            mp3.close()
            await ctx.send("`" + ''.join(c if not (c.isalpha() or c.isnumeric()) else '#' for c in answer) + "`")
            
            await self.game_over(ctx, timeout, self.round_id)
        
        
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
        cursor = self.cursor
        
        offset = 0
        limit = 10
        
        if len(args) > 0:
            try:
                offset = int(args[0])
            except:
                await ctx.send("정수를 입력해주세요!")
                return
        
        if len(args) > 1:
            try:
                limit = int(args[1])
            except:
                await ctx.send("정수를 입력해주세요!")
                return

        if offset < 0 or limit < 0:
            await ctx.send("양수만 입력할 수 있습니다!")
            return
            
        if limit > 10:
            await ctx.send("한번에 10개의 곡만 출력됩니다.")
            limit = 10
        
        # Retrieve quiz settings and songs in the server
        guild_id = ctx.guild.id
        selectQuery = "SELECT * from OsuQuiz where server_id = ? limit ? offset ?;"
        cursor.execute(selectQuery, (guild_id, limit, offset))
        record = cursor.fetchall()
        
        msg = ""
        if len(record) == 0:
            await ctx.send("해당 인덱스의 곡을 찾을 수 없습니다!")
            return
        for i, song in enumerate(record):
            msg += str(i + offset) + ": " + str(song[1]) + " - " + song[2] + "\n"
        
        await ctx.send(msg)
        
        
    @omq.command(name='export')
    async def export_list(self, ctx, *args):
        cursor = self.cursor

        guild_id = ctx.guild.id
        selectQuery = "SELECT * from OsuQuiz where server_id = ?;"
        cursor.execute(selectQuery, (guild_id,))
        record = cursor.fetchall()

        msg = ""
        if len(record) == 0:
            await ctx.send("등록된 곡이 없습니다!")
            return
        for i, song in enumerate(record):
            msg += str(song[1]) + " " + song[2] + "\n"
        
        try:
            file = open("./tmp/texts/omq/backup.txt", "w+")
            n = file.write(msg)
            file.close()
        except:
            await ctx.send("목록 내보내기에 실패했습니다!")
            return

        txt = open("./tmp/texts/omq/backup.txt", 'rb')
        await ctx.send(file=discord.File(fp=txt, filename="songlist.txt"))
        txt.close()


    @omq.command(name='remove')
    async def remove_song(self, ctx, *args):
        cursor = self.cursor
        
        song_id = 0
        try:
            song_id = int(args[0])
        except:
            await ctx.send("곡의 ID를 입력해주세요!")
            return
        
        # Retrieve quiz settings and songs in the server
        guild_id = ctx.guild.id
        deleteQuery = "DELETE from OsuQuiz where server_id = ? and mapset_id = ?;"
        cursor.execute(deleteQuery, (guild_id, song_id))
        record = cursor.rowcount
        
        if record == 0:
            await ctx.send("해당 곡을 지정 곡 목록에서 찾을 수 없습니다!")
        else:
            await ctx.send("해당 곡을 지정 곡 목록에서 삭제했습니다!")

    @omq.command(name='reset')
    async def reset_song(self, ctx, *args):
        cursor = self.cursor
        
        # Retrieve quiz settings and songs in the server
        guild_id = ctx.guild.id
        deleteQuery = "DELETE from OsuQuiz where server_id = ?;"
        cursor.execute(deleteQuery, (guild_id,))
        record = cursor.fetchall()
        
        await ctx.send("서버의 지정곡 목록을 초기화 했습니다!")
       
       
async def answer(message, cursor, omqcog, ctx):
    channel = message.channel
            
    # read pending quiz data
    checkQuery = "SELECT * from OmqRoundAnswer where channel_id = ?;"
    cursor.execute(checkQuery, (channel.id,))
    record = cursor.fetchall()
    
    if len(record) == 0:
        return
     
    answer = message.content.replace(" ", "").lower()
    true_answer = record[0][1].replace(" ", "").lower()
    
    if answer == true_answer:
        # remove quiz from database
        removeQuery = "DELETE from OmqRoundAnswer where channel_id = ?;"
        cursor.execute(removeQuery, (channel.id,))
        
        rowcount = cursor.rowcount
        if rowcount  > 0:
            await channel.send("정답입니다, " + message.author.display_name + "님!")
            await omqcog.play(ctx, True)