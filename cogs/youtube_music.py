import discord
from discord.ext import commands
import yt_dlp as youtube_dl
import asyncio
import os

class YoutubeMusic(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.hybrid_command(name='join', description='Botu ses kanalına davet eder.')
    async def join(self, ctx):
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            if ctx.voice_client is not None:
                return await ctx.voice_client.move_to(channel)
            await channel.connect()
            await ctx.reply("Ses kanalına bağlandım.")
        else:
            await ctx.reply("Lütfen önce bir ses kanalına katılın.")

    @commands.hybrid_command(name='leave', description='Botu ses kanalından çıkarır.')
    async def leave(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.reply("Ses kanalından ayrıldım.")
        else:
            await ctx.reply("Bot herhangi bir ses kanalında değil.")

    @commands.hybrid_command(name='play', description='Belirtilen YouTube videosunun sesini çalar.')
    async def play(self, ctx, *, url: str):
        # Check if the bot is in a voice channel
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.reply("Lütfen önce bir ses kanalına katılın.")
                return
        
        await ctx.defer()  # Let Discord know this might take a while
        
        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'noplaylist': True,
                'quiet': True,
                'no_warnings': True,
                'default_search': 'auto',
                'source_address': '0.0.0.0',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }
            
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                # Handle both search terms and direct URLs
                if not url.startswith(('https://', 'http://')):
                    url = f"ytsearch:{url}"
                
                info = ydl.extract_info(url, download=False)
                
                # Handle playlists vs single videos
                if 'entries' in info:
                    info = info['entries'][0]
                
                audio_url = info['url']
                title = info['title']
                thumbnail = info.get('thumbnail')
                
                # Stop current audio if any
                ctx.voice_client.stop()
                
                # Set audio options
                FFMPEG_OPTIONS = {
                    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                    'options': '-vn',
                }
                
                # Play the audio
                ctx.voice_client.play(discord.FFmpegPCMAudio(audio_url, **FFMPEG_OPTIONS))
                
                # Create embed
                embed = discord.Embed(
                    title="🎵 Şu an çalınıyor",
                    description=f"**{title}**",
                    color=discord.Color.green()
                )
                
                if thumbnail:
                    embed.set_thumbnail(url=thumbnail)
                
                await ctx.reply(embed=embed)
                
        except Exception as e:
            await ctx.reply(f"❌ Müzik çalınırken bir hata oluştu: {str(e)}")

    @commands.hybrid_command(name='pause', description='Çalan müziği duraklatır.')
    async def pause(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.reply("⏸️ Müzik duraklatıldı.")
        else:
            await ctx.reply("Şu anda çalan bir müzik yok.")

    @commands.hybrid_command(name='resume', description='Duraklatılan müziği devam ettirir.')
    async def resume(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.reply("▶️ Müzik devam ediyor.")
        else:
            await ctx.reply("Duraklatılan bir müzik yok.")

    @commands.hybrid_command(name='stop', description='Çalan müziği durdurur.')
    async def stop(self, ctx):
        if ctx.voice_client and (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()):
            ctx.voice_client.stop()
            await ctx.reply("⏹️ Müzik durduruldu.")
        else:
            await ctx.reply("Şu anda çalan bir müzik yok.")

async def setup(bot):
    await bot.add_cog(YoutubeMusic(bot))