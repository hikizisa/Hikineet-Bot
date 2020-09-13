import discord
from discord.ext import commands
import random


class Priconne(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.gacha_colors = (0xc0c0c0, 0xffd700, 0xf0ffff)
        self.priconne_chars = [[], [], []]
        
        with open("priconne.txt", 'r', encoding="utf-8") as f:
            for _, line in enumerate(f):
                parsed = line.split(',')
                if len(parsed) < 3:
                    continue
                self.priconne_chars[int(parsed[2][0])-1].append([parsed[0], parsed[1]])

    @commands.command()
    async def gacha(self, ctx, ren = 10):
        gacha_colors = self.gacha_colors
        priconne_chars = self.priconne_chars

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