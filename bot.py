# bot.py
import signal, sys, os
import sqlite3

import discord
from discord.ext import commands
from dotenv import load_dotenv

from commands.omq import Omq
from commands.basics import Basics
from commands.priconne import Priconne
from commands.osu import Osu

load_dotenv()

TOKEN = os.getenv("TOKEN")
DBPATH = os.getenv("DBPATH")
HOST = os.getenv("HOST")

class Base(commands.Cog):
    def __init__(self, bot, cursor):
        self.bot = bot
        self.cursor = cursor
        self.on_message_callback = []
        
    def more_cog(self, cog):
        if "on_message" in dir(cog):
            self.on_message_callback.append(cog.on_message)
        self.bot.add_cog(cog)

    @commands.Cog.listener()
    async def on_message(self, message):
        for callback in self.on_message_callback:
            await callback(message)


def main():
    try:
        sqliteConnection = sqlite3.connect(DBPATH)
        cursor = sqliteConnection.cursor()
        
        sqlite_select_Query = "select sqlite_version();"
        cursor.execute(sqlite_select_Query)
        record = cursor.fetchall()

    except sqlite3.Error as error:
        sys.exit(0)
 

    def get_prefix(bot, message):
        prefixes = ['?']

        # Check to see if we are outside of a guild. e.g DM's etc.
        if not message.guild:
            # Only allow ? to be used in DMs
            return '?'

        # If we are in a guild, we allow for the user to mention us or use any of the prefixes in our list.
        return commands.when_mentioned_or(*prefixes)(bot, message)

    bot = commands.Bot(command_prefix=get_prefix, description='HikiNeet bot for coding practice', case_insensitive=True)
    
    base_cog = Base(bot, cursor)
    bot.add_cog(base_cog)
    base_cog.more_cog(Omq(bot, cursor))
    base_cog.more_cog(Basics(bot, cursor, sqliteConnection))
    base_cog.more_cog(Osu(bot, cursor))
    base_cog.more_cog(Priconne(bot))
    bot.run(TOKEN)

if __name__ == "__main__":
    main()