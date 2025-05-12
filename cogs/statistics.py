from discord.ext import commands
from database import update_message_stats

class Statistics(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        update_message_stats(message.author.id)

async def setup(bot):
    await bot.add_cog(Statistics(bot))
