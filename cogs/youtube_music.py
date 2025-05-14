import discord
from discord.ext import commands
import yt_dlp as youtube_dl
import asyncio
import concurrent.futures
import os
import logging
import traceback

# Configure logger for this module
logger = logging.getLogger('sezar.music')

class YoutubeMusic(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        logger.info("YoutubeMusic cog initialized")
        
    @commands.hybrid_command(name='join', description='Botu ses kanalına davet eder.')
    async def join(self, ctx):
        try:
            if ctx.author.voice:
                channel = ctx.author.voice.channel
                if ctx.voice_client is not None:
                    await ctx.voice_client.move_to(channel)
                    logger.info(f"Bot moved to voice channel: {channel.name}")
                    return await ctx.reply("Ses kanalına taşındım.")
                await channel.connect()
                logger.info(f"Bot joined voice channel: {channel.name}")
                await ctx.reply("Ses kanalına bağlandım.")
            else:
                logger.warning(f"Join failed: User {ctx.author} not in a voice channel")
                await ctx.reply("Lütfen önce bir ses kanalına katılın.")
        except Exception as e:
            logger.error(f"Error joining voice channel: {str(e)}")
            print(f"❌ Ses kanalına katılma hatası: {str(e)}")
            await ctx.reply(f"Ses kanalına katılırken bir hata oluştu.")

    @commands.hybrid_command(name='leave', description='Botu ses kanalından çıkarır.')
    async def leave(self, ctx):
        try:
            if ctx.voice_client:
                channel_name = ctx.voice_client.channel.name
                await ctx.voice_client.disconnect()
                logger.info(f"Bot left voice channel: {channel_name}")
                await ctx.reply("Ses kanalından ayrıldım.")
            else:
                logger.info("Leave command called but bot not in any voice channel")
                await ctx.reply("Bot herhangi bir ses kanalında değil.")
        except Exception as e:
            logger.error(f"Error leaving voice channel: {str(e)}")
            print(f"❌ Ses kanalından ayrılırken hata: {str(e)}")
            await ctx.reply("Ses kanalından ayrılırken bir hata oluştu.")

    @commands.hybrid_command(name='play', description='Belirtilen YouTube videosunun sesini çalar.')
    async def play(self, ctx, *, url: str):
        try:
            if ctx.voice_client is None:
                if ctx.author.voice:
                    await ctx.author.voice.channel.connect()
                    logger.info(f"Bot joined voice channel for music: {ctx.author.voice.channel.name}")
                else:
                    logger.warning(f"Play failed: User {ctx.author} not in a voice channel")
                    await ctx.reply("Lütfen önce bir ses kanalına katılın.")
                    return
            
            logger.info("Deferring interaction")
            await ctx.defer()  # Defer the interaction to avoid timeout

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

            async def extract_info_async(url):
                loop = asyncio.get_event_loop()
                with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                    return await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))

            logger.info(f"Processing YouTube URL: {url}")
            if not url.startswith(('https://', 'http://')):
                url = f"ytsearch:{url}"
                logger.info(f"Converted to YouTube search: {url}")
            
            info = await extract_info_async(url)
            logger.info("YouTube info extracted")
            
            if 'entries' in info:
                info = info['entries'][0]
            
            audio_url = info['url']
            title = info['title']
            thumbnail = info.get('thumbnail')

            ctx.voice_client.stop()  # Stop current audio if any

            FFMPEG_OPTIONS = {
                'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                'options': '-vn',
            }

            logger.info(f"Starting playback: {title}")
            ctx.voice_client.play(discord.FFmpegPCMAudio(audio_url, **FFMPEG_OPTIONS))

            embed = discord.Embed(
                title="🎵 Şu an çalınıyor",
                description=f"**{title}**",
                color=discord.Color.green()
            )
            if thumbnail:
                embed.set_thumbnail(url=thumbnail)
            
            logger.info("Sending followup message")
            await ctx.followup.send(embed=embed)

        except youtube_dl.utils.DownloadError as e:
            logger.error(f"YouTube download error: {str(e)}")
            await ctx.followup.send(f"❌ Video bulunamadı veya yüklenemedi: {str(e)}")
        except Exception as e:
            logger.error(f"Error playing music: {str(e)}")
            print(f"❌ Müzik çalınırken hata: {str(e)}")
            await ctx.followup.send(f"❌ Müzik çalınırken bir hata oluştu: {str(e)}")

    @commands.hybrid_command(name='pause', description='Çalan müziği duraklatır.')
    async def pause(self, ctx):
        try:
            if ctx.voice_client and ctx.voice_client.is_playing():
                ctx.voice_client.pause()
                logger.info(f"Music paused by {ctx.author}")
                await ctx.reply("⏸️ Müzik duraklatıldı.")
            else:
                logger.info(f"Pause command called but no music is playing")
                await ctx.reply("Şu anda çalan bir müzik yok.")
        except Exception as e:
            logger.error(f"Error pausing music: {str(e)}")
            print(f"❌ Müziği duraklatırken hata: {str(e)}")
            await ctx.reply("Müziği duraklatırken bir hata oluştu.")

    @commands.hybrid_command(name='resume', description='Duraklatılan müziği devam ettirir.')
    async def resume(self, ctx):
        try:
            if ctx.voice_client and ctx.voice_client.is_paused():
                ctx.voice_client.resume()
                logger.info(f"Music resumed by {ctx.author}")
                await ctx.reply("▶️ Müzik devam ediyor.")
            else:
                logger.info(f"Resume command called but no music is paused")
                await ctx.reply("Duraklatılan bir müzik yok.")
        except Exception as e:
            logger.error(f"Error resuming music: {str(e)}")
            print(f"❌ Müziği devam ettirirken hata: {str(e)}")
            await ctx.reply("Müziği devam ettirirken bir hata oluştu.")

    @commands.hybrid_command(name='stop', description='Çalan müziği durdurur.')
    async def stop(self, ctx):
        try:
            if ctx.voice_client and (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()):
                ctx.voice_client.stop()
                logger.info(f"Music stopped by {ctx.author}")
                await ctx.reply("⏹️ Müzik durduruldu.")
            else:
                logger.info(f"Stop command called but no music is playing")
                await ctx.reply("Şu anda çalan bir müzik yok.")
        except Exception as e:
            logger.error(f"Error stopping music: {str(e)}")
            print(f"❌ Müziği durdururken hata: {str(e)}")
            await ctx.reply("Müziği durdururken bir hata oluştu.")

async def setup(bot):
    try:
        await bot.add_cog(YoutubeMusic(bot))
        logger.info("YoutubeMusic cog loaded successfully")
        print("✅ Youtube Music modülü yüklendi")
    except Exception as e:
        logger.error(f"Failed to load YoutubeMusic cog: {str(e)}\n{traceback.format_exc()}")
        print(f"❌ Youtube Music modülü yüklenemedi: {str(e)}")