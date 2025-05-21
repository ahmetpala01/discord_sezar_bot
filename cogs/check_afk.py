import discord
from discord.ext import commands, tasks
import asyncio
from collections import defaultdict

class AFKChecker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.afk_users = {}  # user_id: asyncio.Task
        self.voice_channel_cache = {}  # guild_id: otopark_channel

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        # Kullanıcı ses kanalına katıldı veya self-deafen olduysa
        if after.self_deaf and not before.self_deaf:
            # 5 dakika bekleyen bir görev başlat
            if member.id not in self.afk_users:
                task = asyncio.create_task(self.handle_afk(member))
                self.afk_users[member.id] = task

        # Kullanıcı deaf modundan çıktıysa
        elif not after.self_deaf and before.self_deaf:
            # AFK görevini iptal et
            task = self.afk_users.pop(member.id, None)
            if task:
                task.cancel()

        # Kullanıcı ses kanalından ayrıldıysa
        elif after.channel is None and before.channel is not None:
            # AFK görevini iptal et
            task = self.afk_users.pop(member.id, None)
            if task:
                task.cancel()

    async def handle_afk(self, member: discord.Member):
        try:
            await asyncio.sleep(20)  # 5 dakika bekle
            # Hala deaf durumundaysa
            if member.voice and member.voice.self_deaf:
                otopark_channel = await self.get_otopark_channel(member.guild)
                if otopark_channel and member.voice.channel != otopark_channel:
                    await member.move_to(otopark_channel)
        except asyncio.CancelledError:
            pass
        finally:
            # Temizlik
            self.afk_users.pop(member.id, None)

    async def get_otopark_channel(self, guild: discord.Guild):
        # Cache'e bak
        if guild.id in self.voice_channel_cache:
            return self.voice_channel_cache[guild.id]

        # Kanalı bul
        for channel in guild.voice_channels:
            if channel.name.lower() == "otopark":
                self.voice_channel_cache[guild.id] = channel
                return channel

        print(f"Otopark kanalı {guild.name} sunucusunda bulunamadı.")
        return None

async def setup(bot):
    await bot.add_cog(AFKChecker(bot))
