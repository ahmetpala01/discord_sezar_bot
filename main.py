# main.py

import discord
from discord.ext import commands
import os
import asyncio
import datetime
from dotenv import load_dotenv
from database import init_db

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Tam intents yerine sadece gerekli olanları kullan
intents = discord.Intents.default()
intents.message_content = True  # Mesaj içeriği için gerekli
intents.guilds = True           # Sunucu bilgileri için gerekli
intents.guild_messages = True   # Sunucu mesajları için gerekli
intents.voice_states = True     # Ses özellikleri için gerekli

bot = commands.Bot(command_prefix="/", intents=intents, help_command=None)

# Status mesajları
status_messages = [
    {"type": discord.ActivityType.listening, "message": "Müzik | /play"},
    {"type": discord.ActivityType.playing, "message": "Steam bilgisi | /steamprofil"},
    {"type": discord.ActivityType.watching, "message": "Sorularınızı | /sorusor"},
    {"type": discord.ActivityType.competing, "message": "En hızlı bot | /speedtest"},
]

@bot.event
async def on_ready():
    # Bot başlangıç zamanını kaydet
    bot.start_time = datetime.datetime.now()
    
    print(f"🔗 Giriş yapıldı: {bot.user}")
    
    # Bot durumunu ayarla
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening, 
            name="Müzik | /play | /help"
        ),
        status=discord.Status.online
    )
    
    # Status değiştirme ve istatistik görevlerini başlat
    bot.loop.create_task(change_status())
    bot.loop.create_task(update_stats())
    
    synced = await bot.tree.sync()
    print(f"✅ Slash komutları senkronize edildi: {len(synced)} komut")

async def load_cogs():
    try:
        await bot.load_extension("cogs.steam")
        print("✅ Steam modülü yüklendi")
    except Exception as e:
        print(f"❌ Steam modülü yüklenemedi: {e}")
    try:
        await bot.load_extension("cogs.answers")
        print("✅ Answers modülü yüklendi")
    except Exception as e:
        print(f"❌ Answers modülü yüklenemedi: {e}")
        
    try:
        await bot.load_extension("cogs.youtube_music")
        print("✅ Youtube Music modülü yüklendi")
    except Exception as e:
        print(f"❌ Youtube Music modülü yüklenemedi: {e}")
        
    try:
        await bot.load_extension("cogs.help")
        print("✅ Help modülü yüklendi")
    except Exception as e:
        print(f"❌ Help modülü yüklenemedi: {e}")
        
    try:
        await bot.load_extension("cogs.welcome")
        print("✅ Welcome modülü yüklendi")
    except Exception as e:
        print(f"❌ Welcome modülü yüklenemedi: {e}")
    try:
        await bot.load_extension("cogs.statistics")
        print("✅ Statistics modülü yüklendi")
    except Exception as e:
        print(f"❌ Statistics modülü yüklenemedi: {e}")
    try:
        await bot.load_extension("cogs.moderation")
        print("✅ Moderation modülü yüklendi")
    except Exception as e:
        print(f"❌ Moderation modülü yüklenemedi: {e}")
    try:
        await bot.load_extension("cogs.wordgame")
        print("✅ Wordgame modülü yüklendi")
    except Exception as e:
        print(f"❌ Wordgame modülü yüklenemedi: {e}")
    try:
        await bot.load_extension("cogs.check_afk")
        print("✅ CheckAFK modülü yüklendi")
    except Exception as e:
        print(f"❌ CheckAFK modülü yüklenemedi: {e}")

async def change_status():
    # Bot bağlanana kadar bekle
    await bot.wait_until_ready()
    
    while not bot.is_closed():
        try:
            for status in status_messages:
                # Bot bağlantısı kontrol et
                if bot.is_ready():
                    await bot.change_presence(
                        activity=discord.Activity(
                            type=status["type"],
                            name=status["message"]
                        )
                    )
                await asyncio.sleep(60)  # Her 1 dakikada bir değişim
        except Exception as e:
            print(f"Status değişimi hatası: {e}")
            await asyncio.sleep(60)  # Hata durumunda 60 sn bekle

async def update_stats():
    # Bot bağlanana kadar bekle
    await bot.wait_until_ready()
    
    while not bot.is_closed():
        try:
            # İstatistikleri hesaplayın
            guild_count = len(bot.guilds)
            user_count = sum(guild.member_count for guild in bot.guilds)
            
            # İstatistikleri yazdır
            print(f"Botunuz {guild_count} sunucu ve {user_count} kullanıcıya hizmet veriyor")
            
            # 30 dakikada bir güncelle
            await asyncio.sleep(1800)
        except Exception as e:
            print(f"İstatistik güncelleme hatası: {e}")
            await asyncio.sleep(300)

# Botu başlatmadan önce cogs'ları yükle
async def main():
    async with bot:
        init_db()
        await load_cogs()
        # Not: Task'ları on_ready event'inde başlatıyoruz
        await bot.start(TOKEN)

asyncio.run(main())
