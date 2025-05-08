# main.py

import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    print(f"🔗 Giriş yapıldı: {bot.user}")
    synced = await bot.tree.sync()
    print(f"✅ Slash komutları senkronize edildi: {len(synced)} komut")

async def load_cogs():
    await bot.load_extension("cogs.steam")
    await bot.load_extension("cogs.speedtest")

# Botu başlatmadan önce cogs'ları yükle
async def main():
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)

import asyncio
asyncio.run(main())
