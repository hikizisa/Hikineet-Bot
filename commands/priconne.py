import discord
from discord.ext import commands
import random
import os
import requests
from PIL import Image


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

        limit = 50

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
            
        res_str = ''
        res_images = []
        priconne_img_dir = "./tmp/imgs/priconne/"
        
        if not os.path.exists(priconne_img_dir):
            os.makedirs(priconne_img_dir)
            
        for i, char in enumerate(result):
            image = "./tmp/imgs/priconne/"+char[0]+".png"

            if not os.path.exists(image):
                response = requests.get(char[1])
                print(response)
                char_img = open(image, "wb")
                char_img.write(response.content)
                char_img.close()
            
            res_images.append(Image.open(image))
            res_str += char[0] + "(" + str(char[2] + 1) + "성) "
            if i % 5 == 4:
                res_str += "\n"

        widths, heights = zip(*(i.size for i in res_images))
        total_width = widths[0] * (5 if ren >= 5 else ren)
        total_height = heights[0] * ((ren-1) // 5 + 1)
        
        gacha_result = Image.new('RGB', (total_width, total_height))
        
        for i, img in enumerate(res_images):
            gacha_result.paste(img, (i % 5 * widths[0], i // 5 * widths[0]))
        
        res_image_path = "./tmp/imgs/priconne/result.jpg"
        gacha_result.save(res_image_path)
        
        image = open(res_image_path, 'rb')
        await ctx.send(file=discord.File(fp=image, filename="result.jpg"), content=res_str)
        image.close()
        
        os.remove(res_image_path)
            
            