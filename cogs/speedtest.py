# cogs/speedtest.py

import discord
from discord.ext import commands
import speedtest

class SpeedTest(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="speedtest", description="İnternet hızını ölçer")
    async def speedtest_command(self, ctx):
        await ctx.reply("⏳ Hız testi yapılıyor, lütfen bekleyin...")

        st = speedtest.Speedtest()
        st.get_best_server()
        download_speed = st.download() / 1_000_000
        upload_speed = st.upload() / 1_000_000
        ping = st.results.ping

        embed = discord.Embed(title="📶 İnternet Hızı Sonuçları", color=0x1abc9c)
        embed.add_field(name="⬇️ İndirme Hızı", value=f"{download_speed:.2f} Mbps", inline=False)
        embed.add_field(name="⬆️ Yükleme Hızı", value=f"{upload_speed:.2f} Mbps", inline=False)
        embed.add_field(name="🏓 Ping", value=f"{ping:.2f} ms", inline=False)

        await ctx.reply(embed=embed)

async def setup(bot):
    await bot.add_cog(SpeedTest(bot))
