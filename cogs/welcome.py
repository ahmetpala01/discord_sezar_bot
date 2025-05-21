# cogs/welcome.py
import discord
from discord.ext import commands
import random
import asyncio
from datetime import datetime

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.version = "1.0.0"
        self.support_server = "https://discord.com/oauth2/authorize?client_id=1372553389539328151"
        
        # Hoş geldin mesajları çeşitleri
        self.welcome_messages = [
            "🎉 Aramıza hoş geldin {user}! Seni burada görmek harika!",
            "🌟 {user} topluluğumuza katıldı! Merhaba ve hoş geldin!",
            "🚀 {user} sunucuya iniş yaptı! Hoş geldin!",
            "✨ {user} bize katıldı! Merhaba ve sunucumuza hoş geldin!",
            "🔥 {user} topluluğa katıldı! Seninle tanışmak için sabırsızlanıyoruz!"
        ]

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """Bot bir sunucuya eklendiğinde çalışır"""
        # Mesaj gönderilecek uygun kanalı bul (genel sohbet, hoşgeldin, bot komutları vb.)
        channel = None
        
        # Önce "genel", "sohbet", "hoşgeldin" veya "bot" içeren kanalları ara
        for ch in guild.text_channels:
            channel_name = ch.name.lower()
            if any(name in channel_name for name in ["genel", "chat", "sohbet", "hoşgeldin", "welcome", "bot"]):
                if ch.permissions_for(guild.me).send_messages:
                    channel = ch
                    break
        
        # Eğer uygun kanal bulunamadıysa, yazma izni olan ilk kanalı seç
        if not channel:
            for ch in guild.text_channels:
                if ch.permissions_for(guild.me).send_messages:
                    channel = ch
                    break
        
        if channel:
            embed = discord.Embed(
                title="👋 Sezar Bot Sunucunuza Katıldı!",
                description=f"Merhaba {guild.name}! Beni sunucunuza eklediğiniz için teşekkürler!",
                color=discord.Color.gold()
            )
            
            embed.add_field(
                name="🚀 Başlangıç",
                value="Komutlarımı görmek için `/help` komutunu kullanabilirsiniz.\n"
                     "Herhangi bir komut hakkında detaylı bilgi için `/help <komut>` yazabilirsiniz.",
                inline=False
            )
            
            embed.add_field(
                name="🎵 Müzik Komutları",
                value="YouTube'dan müzik çalmak için: `/play <şarkı adı>`\n"
                     "Müziği durdurmak için: `/stop`",
                inline=False
            )
            
            embed.add_field(
                name="💬 Sohbet Özellikleri",
                value="Sohbet etmek için: `/sohbet <mesaj>`\n"
                     "Veya beni direkt etiketleyebilirsiniz: `@Sezar Bot <mesaj>`",
                inline=False
            )
            
            embed.add_field(
                name="🛠️ Diğer Özellikler",
                value="Steam profilleri: `/steamprofil <kullanıcı_adı>`\n"
                     "İnternet hız testi: `/speedtest`",
                inline=False
            )
            
            embed.add_field(
                name="🔧 Destek", 
                value=f"Herhangi bir sorun veya öneriniz varsa, [destek sunucumuza]({self.support_server}) katılabilirsiniz.", 
                inline=False
            )
            
            # Görsel öğeler
            embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user.avatar else "")
            embed.set_footer(text=f"Sezar Bot v{self.version} | /help komutu ile tüm komutları görebilirsiniz")
            embed.timestamp = datetime.utcnow()
            
            await channel.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Bir kullanıcı sunucuya katıldığında çalışır"""
        # Sunucudan hoşgeldin kanalını bul
        welcome_channel = None
        
        # Özel hoşgeldin kanalı ara
        for channel in member.guild.text_channels:
            channel_name = channel.name.lower()
            if any(word in channel_name for word in ["hoşgeldin", "welcome", "giriş", "join"]):
                if channel.permissions_for(member.guild.me).send_messages:
                    welcome_channel = channel
                    break
        
        # Hoşgeldin kanalı yoksa genel kanalı seç
        if not welcome_channel:
            for channel in member.guild.text_channels:
                if channel.permissions_for(member.guild.me).send_messages:
                    welcome_channel = channel
                    break
        
        # Kanal bulunmadıysa fonksiyonu sonlandır
        if not welcome_channel:
            return
            
        # Rastgele bir hoşgeldin mesajı seç
        welcome_message = random.choice(self.welcome_messages).format(user=member.mention)
        
        # Sunucuya katılan kaçıncı üye olduğunu hesapla
        member_number = len([m for m in member.guild.members if not m.bot])
        
        embed = discord.Embed(
            title="🎉 Yeni Üye!",
            description=f"{welcome_message}\n\n{member.guild.name} sunucusuna katılan {member_number}. üyesin!",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="📜 Öneriler",
            value=f"• Kuralları okumayı unutma\n"
                  f"• Kendini tanıtabilirsin\n"
                  f"• Komutlarımı görmek için `/help` yaz",
            inline=False
        )
        
        # Kullanıcı avatarı ve sunucu bilgileri
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.set_footer(text=f"{member.guild.name} | Katılma Tarihi")
        embed.timestamp = member.joined_at
        
        welcome_msg = await welcome_channel.send(embed=embed)
        
        # Hoşgeldin mesajına emoji reaksiyonu ekle
        try:
            await welcome_msg.add_reaction("👋")
            await asyncio.sleep(0.5)
            await welcome_msg.add_reaction("🎉")
        except discord.errors.Forbidden:
            pass
    
    @commands.hybrid_command(name="sunucubilgi", description="Sunucu hakkında bilgi verir")
    async def server_info(self, ctx):
        """Sunucu hakkında detaylı bilgi verir"""
        guild = ctx.guild
        
        # Online/offline üye sayılarını hesapla
        total_members = guild.member_count
        online_members = len([m for m in guild.members if m.status != discord.Status.offline and not m.bot])
        bot_count = len([m for m in guild.members if m.bot])
        
        # Sunucu özellikleri
        features_list = []
        for feature in guild.features:
            feature_name = feature.replace('_', ' ').title()
            features_list.append(f"✓ {feature_name}")
        
        features_text = "\n".join(features_list) if features_list else "Özel özellik bulunmuyor"
        
        # Oluşturma tarihini ve süreyi hesapla
        created_date = guild.created_at.strftime("%d/%m/%Y")
        created_time = guild.created_at.strftime("%H:%M:%S")
        delta = datetime.now(datetime.timezone.utc) - guild.created_at
        days = delta.days
        
        embed = discord.Embed(
            title=f"📊 {guild.name} Sunucu Bilgileri",
            description=f"{guild.description or 'Sunucu açıklaması yok'}",
            color=discord.Color.blue()
        )
        
        # Temel bilgiler
        embed.add_field(name="🆔 Sunucu ID", value=f"`{guild.id}`", inline=True)
        embed.add_field(name="👑 Sunucu Sahibi", value=guild.owner.mention if guild.owner else "Bulunamadı", inline=True)
        embed.add_field(name="🌍 Bölge", value=str(guild.preferred_locale).replace('-', ' ').title(), inline=True)
        
        # Üye istatistikleri
        embed.add_field(name="👥 Toplam Üye", value=f"`{total_members:,}`", inline=True)
        embed.add_field(name="🟢 Çevrimiçi Üye", value=f"`{online_members:,}`", inline=True)
        embed.add_field(name="🤖 Bot Sayısı", value=f"`{bot_count:,}`", inline=True)
        
        # Kanal istatistikleri
        embed.add_field(name="💬 Metin Kanalları", value=f"`{len(guild.text_channels):,}`", inline=True)
        embed.add_field(name="🔊 Ses Kanalları", value=f"`{len(guild.voice_channels):,}`", inline=True)
        embed.add_field(name="📁 Kategoriler", value=f"`{len(guild.categories):,}`", inline=True)
        
        # Emoji ve rol istatistikleri
        embed.add_field(name="😄 Emoji Sayısı", value=f"`{len(guild.emojis):,}`", inline=True)
        embed.add_field(name="🏷️ Rol Sayısı", value=f"`{len(guild.roles):,}`", inline=True)
        embed.add_field(name="📆 Oluşturulma Süresi", value=f"`{days:,} gün`", inline=True)
        
        # Ekstra bilgiler
        if len(features_list) > 0:
            embed.add_field(name="✨ Özel Özellikler", value=features_text, inline=False)
        
        embed.add_field(
            name="📅 Oluşturulma Tarihi", 
            value=f"`{created_date}` tarihinde `{created_time}` saatinde oluşturuldu", 
            inline=False
        )
        
        # Sunucu resmi
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        # Banner varsa banner'ı göster
        if guild.banner:
            embed.set_image(url=guild.banner.url)
            
        embed.set_footer(text=f"Sezar Bot v{self.version} | {ctx.author} tarafından istendi")
        embed.timestamp = datetime.now(datetime.timezone.utc)
        
        await ctx.reply(embed=embed)

async def setup(bot):
    await bot.add_cog(Welcome(bot))