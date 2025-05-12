# cogs/help.py

import datetime
import platform
import discord
from discord.ext import commands
import os

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.version = "1.0.0"  # Bot versiyonu
        self.github_repo = "https://github.com/ibrahimsezer/discord_sezar_bot"  # GitHub repo adresiniz
        self.support_invite = "https://discord.com/oauth2/authorize?client_id=1369772830937317437"  # Destek sunucusu davet bağlantınız
        self.bot_invite = f"https://discord.com/oauth2/authorize?client_id=1369772830937317437"
    
    @commands.hybrid_command(name="help", description="Tüm komutları gösterir")
    async def help_command(self, ctx, *, command: str = None):
        """
        Yardım menüsü - belirli bir komut belirtilirse o komut hakkında detaylı bilgi verir
        """
        if command:
            return await self.show_command_help(ctx, command)
        
        embed = discord.Embed(
            title="🤖 Sezar Bot - Yardım Menüsü", 
            description="Sezar Bot, Discord sunucunuz için müzik, sohbet ve araç özellikleri sunan çok amaçlı bir bottur.\n\n"
                       "`/help <komut>` yazarak herhangi bir komut hakkında daha fazla bilgi alabilirsiniz.",
            color=discord.Color.blue()
        )
        
        # Bot bilgisi
        embed.add_field(
            name="🔍 Bot Bilgisi",
            value=f"Sürüm: `v{self.version}`\n"
                  f"Prefix: `/`\n"
                  f"Sunucu Sayısı: `{len(self.bot.guilds)}`\n"
                  f"Ping: `{round(self.bot.latency * 1000)}ms`",
            inline=False
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
        
        # Sohbet Komutları
        embed.add_field(
            name="💬 Sohbet Komutları",
            value="`/sorusor` - Sorularınızı cevaplayacak\n"
                  "`/sohbet` - Botla sohbet edersiniz\n"
                  "@Sezar Bot - Botu direkt etiketleyerek de konuşabilirsiniz",
            inline=False
        )
        
        # Araçlar
        embed.add_field(
            name="🛠️ Araçlar",
            value="`/steamprofil` - Steam profil bilgilerini gösterir\n"
                  "`/speedtest` - İnternet hız testi yapar\n"
                  "`/botbilgi` - Bot hakkında detaylı teknik bilgileri gösterir",
            inline=False
        )
        
        # Moderasyon Komutları
        embed.add_field(
            name="🔒 Moderasyon Komutları",
            value="`/ban` - Kullanıcıyı sunucudan yasaklar\n"
                  "`/kick` - Kullanıcıyı sunucudan atar\n"
                  "`/clear` - Belirtilen sayıda mesajı siler",
            inline=False
        )
        
        # İstatistik Komutları
        embed.add_field(
            name="📊 İstatistik Komutları",
            value="`/stats` - Sunucu istatistiklerini gösterir\n"
                  "`/userstats` - Kullanıcı istatistiklerini gösterir",
            inline=False
        )
        
        # Linkler
        embed.add_field(
            name="🔗 Bağlantılar",
            value=f"[Bot'u Davet Et]({self.bot_invite}) | [Destek Sunucusu]({self.support_invite}) | [GitHub]({self.github_repo})",
            inline=False
        )
        
        # Footer bilgisi ve thumbnail
        embed.set_footer(text=f"Sezar Bot v{self.version} | Geliştirici: joulesezarwatt")
        if self.bot.user and self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        
        await ctx.reply(embed=embed)
    
    async def show_command_help(self, ctx, command_name):
        """Belirli bir komut hakkında detaylı bilgi gösterir"""
        commands_info = {
            "play": {
                "description": "YouTube'dan müzik çalar",
                "usage": "/play <şarkı adı veya URL>",
                "example": "/play Daft Punk Get Lucky",
                "category": "🎵 Müzik",
                "permissions": "Ses kanalına bağlanma"
            },
            "pause": {
                "description": "Çalan müziği duraklatır",
                "usage": "/pause",
                "example": "/pause",
                "category": "🎵 Müzik",
                "permissions": "Yok"
            },
            "resume": {
                "description": "Duraklatılmış müziği devam ettirir",
                "usage": "/resume",
                "example": "/resume",
                "category": "🎵 Müzik",
                "permissions": "Yok"
            },
            "stop": {
                "description": "Çalan müziği tamamen durdurur",
                "usage": "/stop",
                "example": "/stop",
                "category": "🎵 Müzik",
                "permissions": "Yok"
            },
            "join": {
                "description": "Botu bulunduğunuz ses kanalına davet eder",
                "usage": "/join",
                "example": "/join",
                "category": "🎵 Müzik",
                "permissions": "Ses kanalına bağlı olma"
            },
            "leave": {
                "description": "Botu ses kanalından çıkarır",
                "usage": "/leave",
                "example": "/leave",
                "category": "🎵 Müzik",
                "permissions": "Yok"
            },
            "sorusor": {
                "description": "Sezar Bot'a bir soru sorarsınız",
                "usage": "/sorusor <soru>",
                "example": "/sorusor Bugün hava nasıl olacak?",
                "category": "💬 Sohbet",
                "permissions": "Yok"
            },
            "sohbet": {
                "description": "Sezar Bot ile sohbet edersiniz",
                "usage": "/sohbet <mesaj>",
                "example": "/sohbet Merhaba, nasılsın?",
                "category": "💬 Sohbet",
                "permissions": "Yok"
            },
            "steamprofil": {
                "description": "Belirtilen Steam kullanıcı adına ait profil bilgilerini gösterir",
                "usage": "/steamprofil <kullanıcı_adı>",
                "example": "/steamprofil gabelogannewell",
                "category": "🛠️ Araçlar",
                "permissions": "Yok"
            },
            "speedtest": {
                "description": "Botun bulunduğu sunucudan internet hız testi yapar",
                "usage": "/speedtest",
                "example": "/speedtest",
                "category": "🛠️ Araçlar",
                "permissions": "Yok"
            },
            "botbilgi": {
                "description": "Sezar Bot hakkında teknik bilgileri gösterir",
                "usage": "/botbilgi",
                "example": "/botbilgi",
                "category": "🛠️ Araçlar",
                "permissions": "Yok"
            },
            "ban": {
                "description": "Belirtilen kullanıcıyı sunucudan yasaklar",
                "usage": "/ban <@kullanıcı> [sebep]",
                "example": "/ban @KullanıcıAdı Kurallara uymama",
                "category": "🔒 Moderasyon",
                "permissions": "Üyeleri Yasakla"
            },
            "kick": {
                "description": "Belirtilen kullanıcıyı sunucudan atar",
                "usage": "/kick <@kullanıcı> [sebep]",
                "example": "/kick @KullanıcıAdı Uygunsuz davranış",
                "category": "🔒 Moderasyon",
                "permissions": "Üyeleri At"
            },
            "clear": {
                "description": "Belirtilen sayıda mesajı siler",
                "usage": "/clear <sayı>",
                "example": "/clear 10",
                "category": "🔒 Moderasyon",
                "permissions": "Mesajları Yönet"
            },
            "help": {
                "description": "Komutlar hakkında yardım gösterir",
                "usage": "/help [komut]",
                "example": "/help play",
                "category": "ℹ️ Bilgi",
                "permissions": "Yok"
            },
            "stats": {
                "description": "Sunucu istatistiklerini gösterir",
                "usage": "/stats",
                "example": "/stats",
                "category": "📊 İstatistik",
                "permissions": "Yok"
            },
            "userstats": {
                "description": "Kullanıcı istatistiklerini gösterir",
                "usage": "/userstats [@kullanıcı]",
                "example": "/userstats @KullanıcıAdı",
                "category": "📊 İstatistik",
                "permissions": "Yok"
            }
        }
        
        # Komut bilgisi mevcut mu kontrol et
        if command_name.lower() not in commands_info:
            return await ctx.reply(f"❌ `{command_name}` komutu hakkında bilgi bulunamadı.")
        
        # Komut bilgilerini al
        cmd_info = commands_info[command_name.lower()]
        
        # Embed oluştur
        embed = discord.Embed(
            title=f"/{command_name} Komutu",
            description=cmd_info["description"],
            color=discord.Color.blue()
        )
        
        embed.add_field(name="📋 Kategori", value=cmd_info["category"], inline=False)
        embed.add_field(name="🔍 Kullanım", value=f"`{cmd_info['usage']}`", inline=False)
        embed.add_field(name="📝 Örnek", value=f"`{cmd_info['example']}`", inline=False)
        
        if cmd_info["permissions"] != "Yok":
            embed.add_field(name="🔒 Gerekli İzinler", value=cmd_info["permissions"], inline=False)
        
        embed.set_footer(text=f"Sezar Bot v{self.version} | Prefix: /")
        
        await ctx.reply(embed=embed)
    
    @commands.hybrid_command(name="botbilgi", description="Bot hakkında teknik bilgileri gösterir")
    async def show_bot_info(self, ctx):
        """Bot hakkında teknik bilgileri gösterir"""
        # Bot başlangıç zamanını kontrol et
        if not hasattr(self.bot, 'start_time'):
            # Eğer start_time tanımlanmadıysa
            uptime = "Tanımlanmadı"
        else:
            uptime = str(datetime.datetime.now() - self.bot.start_time).split('.')[0]
            
        bot_latency = round(self.bot.latency * 1000)  # ms cinsinden
        
        embed = discord.Embed(
            title="ℹ️ Sezar Bot - Teknik Bilgiler",
            description=f"Sezar Bot v{self.version}, Discord sunucunuz için tasarlanmış çok amaçlı bir bottur.",
            color=discord.Color.blue()
        )
        
        # Sunucu ve Kullanıcı İstatistikleri
        embed.add_field(name="📊 Sunucu Sayısı", value=f"{len(self.bot.guilds):,}", inline=True)
        total_users = sum(g.member_count for g in self.bot.guilds)
        embed.add_field(name="👥 Toplam Kullanıcı", value=f"{total_users:,}", inline=True)
        embed.add_field(name="🌐 Shard Sayısı", value=f"{self.bot.shard_count or 1}", inline=True)
        
        # Performans Bilgileri
        embed.add_field(name="📡 Gecikme", value=f"{bot_latency}ms", inline=True)
        embed.add_field(name="⏱️ Çalışma Süresi", value=uptime, inline=True)
        
        # Teknik Bilgiler
        embed.add_field(name="🤖 Bot ID", value=f"{self.bot.user.id}", inline=True)
        embed.add_field(name="🔧 Discord.py", value=f"v{discord.__version__}", inline=True)
        embed.add_field(name="🐍 Python", value=f"v{platform.python_version()}", inline=True)
        embed.add_field(name="💻 İşletim Sistemi", value=f"{platform.system()} {platform.release()}", inline=True)
        
        # Bağlantılar
        embed.add_field(
            name="🔗 Bağlantılar",
            value=f"[Bot'u Davet Et]({self.bot_invite}) | [Destek Sunucusu]({self.support_invite}) | [GitHub]({self.github_repo})",
            inline=False
        )
        
        # Footer ve Thumbnail
        embed.set_footer(text="Geliştirici: joulesezarwatt | Son Güncelleme: 01.05.2025")
        if self.bot.user and self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        
        await ctx.reply(embed=embed)
        
    @commands.hybrid_command(name="davet", description="Bot'u sunucunuza davet etmek için bağlantı verir")
    async def invite(self, ctx):
        """Bot'u sunucunuza davet etmek için bağlantı verir"""
        embed = discord.Embed(
            title="🤖 Sezar Bot'u Davet Et!",
            description="Aşağıdaki bağlantıya tıklayarak Sezar Bot'u kendi sunucunuza ekleyebilirsiniz.",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="📩 Davet Bağlantısı",
            value=f"[Sezar Bot'u Ekle]({self.bot_invite})",
            inline=False
        )
        
        embed.add_field(
            name="🔗 Diğer Bağlantılar",
            value=f"[Destek Sunucusu]({self.support_invite}) | [GitHub]({self.github_repo})",
            inline=False
        )
        
        embed.set_footer(text=f"Sezar Bot v{self.version} | Geliştirici: joulesezarwatt")
        if self.bot.user and self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
            
        await ctx.reply(embed=embed)

async def setup(bot):
    await bot.add_cog(Help(bot))