# cogs/welcome.py dosyası
import discord
from discord.ext import commands

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        # Mesaj gönderilecek uygun kanalı bul
        channel = None
        for ch in guild.text_channels:
            if ch.permissions_for(guild.me).send_messages:
                channel = ch
                break
        
        if channel:
            embed = discord.Embed(
                title="👋 Merhaba! Sezar Bot Burada!",
                description="Beni sunucunuza eklediğiniz için teşekkürler!",
                color=discord.Color.gold()
            )
            
            embed.add_field(
                name="🚀 Başlamak İçin",
                value="Komutların listesini görmek için `/help` komutunu kullanabilirsiniz.",
                inline=False
            )
            
            embed.add_field(
                name="🔧 Destek", 
                value="Herhangi bir sorun veya öneriniz varsa, [destek sunucumuza](https://discord.gg/YOUR_INVITE) katılabilirsiniz.", 
                inline=False
            )
            
            embed.set_footer(text="🎵 Müzik, 🎮 Oyun, 💬 Sohbet ve daha fazlası!")
            
            await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Welcome(bot))