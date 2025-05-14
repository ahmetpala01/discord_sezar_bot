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
    
    # Force sync all application commands
    await sync_all_commands()

async def sync_all_commands():
    try:
        print("Slash komutları senkronize ediliyor...")
        synced = await bot.tree.sync()
        print(f"✅ Global slash komutları senkronize edildi: {len(synced)} komut")
        return synced
    except Exception as e:
        print(f"❌ Komut senkronizasyonu hatası: {e}")
        return []
    
    
@bot.command(name="sync")
@commands.is_owner()  # Only bot owner can use this command
async def sync_command(ctx):
    """Manually sync slash commands with Discord"""
    try:
        await ctx.send("Syncing slash commands...")
        synced = await bot.tree.sync()
        await ctx.send(f"✅ Synced {len(synced)} slash commands to Discord!")
    except Exception as e:
        await ctx.send(f"❌ Error syncing commands: {e}")

async def load_cogs():
    """Load all cogs and ensure commands are registered"""
    # Dictionary to track loaded extensions and their command counts
    cog_stats = {}
    
    # List of all cogs to load
    cogs_to_load = [
        "cogs.steam", 
        "cogs.answers",
        "cogs.youtube_music", 
        "cogs.help",
        "cogs.welcome", 
        "cogs.statistics",
        "cogs.moderation", 
        "cogs.wordgame",
        "cogs.check_afk",
        "cogs.speedtest"  # Make sure this is included if it exists
    ]
    
    # Track command count before loading
    cmd_count_before = len(bot.tree.get_commands())
    
    # Load each cog
    for cog in cogs_to_load:
        try:
            # Store command count before loading this cog
            before_count = len(bot.tree.get_commands())
            
            # Load the cog
            await bot.load_extension(cog)
            
            # Calculate how many commands were added by this cog
            after_count = len(bot.tree.get_commands())
            cmd_added = after_count - before_count
            
            # Track stats
            cog_name = cog.split(".")[-1].capitalize()
            cog_stats[cog] = cmd_added
            
            print(f"✅ {cog_name} modülü yüklendi (+{cmd_added} komut)")
        except Exception as e:
            print(f"❌ {cog.split('.')[-1].capitalize()} modülü yüklenemedi: {e}")
    
    # Calculate total commands added
    cmd_count_after = len(bot.tree.get_commands())
    total_added = cmd_count_after - cmd_count_before
    
    print(f"📊 Toplam {total_added} komut yüklendi")
    
    # Debug information - List all commands by cog
    if cog_stats:
        print("\n🔍 Cog bazında komut dağılımı:")
        for cog, count in cog_stats.items():
            print(f"  • {cog.split('.')[-1].capitalize()}: {count} komut")
    
    return cog_stats

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
