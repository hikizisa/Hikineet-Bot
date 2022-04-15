import nextcord
from nextcord.ext import commands
from deep_translator import GoogleTranslator
            
class Translate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='translate')
    async def translate(self, ctx, *args):
        lang = args[0]
        msg = " ".join(args[1:])
        
        if lang.lower() == 'list':
            await ctx.send(GoogleTranslator.get_supported_languages(as_dict=True))
            return

        try:
            translated = GoogleTranslator(source='auto', target=lang).translate(msg)
            await ctx.send(translated)
        except:
            await ctx.send("지원되지 않는 언어입니다.")
        