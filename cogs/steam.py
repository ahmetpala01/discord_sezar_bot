# cogs/steam.py

import discord
from discord.ext import commands
import requests
import os

class Steam(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.STEAM_API_KEY = os.getenv("STEAM_API_KEY")

    @commands.hybrid_command(name="steamprofil", description="Steam kullanıcı adı ile profil bilgilerini getirir")
    async def steam_profile(self, ctx, username: str):
        await ctx.reply("🔍 Kullanıcı bilgileri alınıyor...")

        url = f"http://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/?key={self.STEAM_API_KEY}&vanityurl={username}"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            steamid64 = data.get('response', {}).get('steamid', None)

            if steamid64:
                profile_url = f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={self.STEAM_API_KEY}&steamids={steamid64}"
                profile_response = requests.get(profile_url)

                if profile_response.status_code == 200:
                    player = profile_response.json().get("response", {}).get("players", [])[0]

                    embed = discord.Embed(
                        title=f"👤 {player.get('personaname', 'Bilinmiyor')}",
                        url=player.get("profileurl", ""),
                        description="Steam profil bilgileri",
                        color=discord.Color.blue()
                    )
                    embed.set_thumbnail(url=player.get("avatarfull", ""))
                    embed.add_field(name="Gerçek İsim", value=player.get("realname", "Yok"), inline=True)
                    embed.add_field(name="Ülke", value=player.get("loccountrycode", "Yok"), inline=True)
                    embed.add_field(name="Durum", value=str(player.get("personastate", "0")), inline=True)

                    await ctx.reply(embed=embed)
                else:
                    await ctx.reply("❌ Profil verisi alınamadı.")
            else:
                await ctx.reply("❌ Geçersiz kullanıcı adı.")
        else:
            await ctx.reply("⚠️ Steam API bağlantı hatası.")

async def setup(bot):
    await bot.add_cog(Steam(bot))
