# cogs/help.py

import datetime
import platform
import discord
from discord.ext import commands

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.hybrid_command(name="help", description="Tüm komutları gösterir")
    async def help_command(self, ctx):
        embed = discord.Embed(
            title="📋 Sezar Bot - Komut Listesi", 
            description="İşte kullanabileceğiniz tüm komutlar:", 
            color=discord.Color.blue()
        )
        
        # Müzik Komutları
        embed.add_field(
            name="🎵 Müzik Komutları",
            value="`/play` - YouTube'dan müzik çalar\n"
                  "`/pause` - Müziği duraklatır\n"
                  "`/resume` - Müziği devam ettirir\n"
                  "`/stop` - Müziği durdurur\n"
                  "`/join` - Ses kanalına katılır\n"
                  "`/leave` - Ses kanalından ayrılır",
            inline=False
        )
        
        # Genel Komutlar
        embed.add_field(
            name="💬 Sohbet Komutları",
            value="`/sorusor` - Sorularınızı cevaplayacak\n"
                  "`/sohbet` - Botla sohbet edersiniz",
            inline=False
        )
        
        # Araçlar
        embed.add_field(
            name="🛠️ Araçlar",
            value="`/steamprofil` - Steam profil bilgilerini gösterir\n"
                  "`/speedtest` - İnternet hız testi yapar\n"
                  "`/botbilgi` - Bot hakkında bilgi verir",
            inline=False
        )
        
        # Footer bilgisi
        embed.set_footer(text=f"Prefix: / | Sunucu Sayısı: {len(self.bot.guilds)}")
        
        await ctx.reply(embed=embed)
    
    @commands.hybrid_command(name="botbilgi", description="Bot hakkında teknik bilgileri gösterir")
    async def show_bot_info(self, ctx):
        # Bot başlangıç zamanını kontrol et
        if not hasattr(self.bot, 'start_time'):
            # Eğer start_time tanımlanmadıysa
            uptime = "Tanımlanmadı"
        else:
            uptime = str(datetime.datetime.now() - self.bot.start_time).split('.')[0]
            
        bot_latency = round(self.bot.latency * 1000)  # ms cinsinden
        
        embed = discord.Embed(
            title="ℹ️ Sezar Bot - Teknik Bilgiler",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="📊 Sunucu Sayısı", value=f"{len(self.bot.guilds)}", inline=True)
        embed.add_field(name="👥 Toplam Kullanıcı", value=f"{sum(g.member_count for g in self.bot.guilds)}", inline=True)
        embed.add_field(name="📡 Gecikme", value=f"{bot_latency}ms", inline=True)
        embed.add_field(name="⏱️ Çalışma Süresi", value=uptime, inline=True)
        embed.add_field(name="🔧 Discord.py Sürümü", value=discord.__version__, inline=True)
        embed.add_field(name="🐍 Python Sürümü", value=platform.python_version(), inline=True)
        
        embed.set_footer(text="Bot Yapımcısı: joulesezarwatt")
        
        await ctx.reply(embed=embed)

async def setup(bot):
    await bot.add_cog(Help(bot))