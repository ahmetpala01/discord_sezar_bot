import discord
from discord.ext import commands
import yt_dlp as youtube_dl
import asyncio
import os
import logging
import traceback
import platform
import subprocess
import shutil
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
import ffmpeg  # Import the ffmpeg-python library
import sys
import io
import wave
import numpy as np
from discord import PCMVolumeTransformer
from discord.opus import Encoder as OpusEncoder

# Configure logger for this module
logger = logging.getLogger('sezar.music')

class FFmpegPCMAudio(discord.AudioSource):
    """Audio source for ffmpeg-python library"""
    def __init__(self, source, *, executable=None, pipe=False, stderr=None, before_options=None, options=None):
        self.source = source
        self.executable = executable or 'ffmpeg'
        self.pipe = pipe
        self.stderr = stderr
        self.before_options = before_options or ''
        self.options = options or ''
        self.process = None
        self.stdout = None
        self.block_size = OpusEncoder.FRAME_SIZE * 4  # 4 bytes per sample for 16-bit stereo
        
        # Try to find ffmpeg binary
        self._locate_ffmpeg()

    def _locate_ffmpeg(self):
        """Locate ffmpeg binary on the system"""
        try:
            # First check if it's in the system path
            if shutil.which('ffmpeg'):
                self.executable = 'ffmpeg'
                return True
                
            # Check common Windows locations
            if platform.system() == 'Windows':
                possible_paths = [
                    r'C:\ffmpeg\bin\ffmpeg.exe',
                    r'C:\Program Files\ffmpeg\bin\ffmpeg.exe',
                    r'C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe',
                ]
                
                for path in possible_paths:
                    if os.path.isfile(path):
                        self.executable = path
                        return True
            
            # Fall back to PATH
            return False
        except Exception as e:
            logger.error(f"Error locating ffmpeg: {str(e)}")
            return False

    def _create_process(self):
        try:
            args = []
            
            # Add the FFmpeg executable
            args.append(self.executable)
            
            # Add before options if they exist
            if self.before_options:
                args.extend(self.before_options.split())
                
            # Add input
            args.extend(['-i', self.source])
            
            # Add output options
            args.extend(['-f', 's16le',
                         '-ar', '48000',
                         '-ac', '2',
                         '-loglevel', 'warning'])
            
            # Add user options if they exist
            if self.options:
                args.extend(self.options.split())
            
            # Add pipe output
            args.append('pipe:1')
            
            logger.debug(f"FFmpeg command: {' '.join(args)}")
            
            # Create the process
            self.process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE if not self.pipe else subprocess.STDOUT
            )
            
            self.stdout = self.process.stdout
            
        except FileNotFoundError:
            logger.error(f"FFmpeg executable not found: {self.executable}")
            raise
        except Exception as e:
            logger.error(f"Error creating ffmpeg process: {str(e)}")
            if self.process:
                self.process.kill()
            raise e

    def read(self):
        if self.process is None:
            self._create_process()

        try:
            # Read bytes from stdout of the ffmpeg process
            data = self.stdout.read(self.block_size)
            
            if not data:
                # End of the stream
                self.cleanup()
                return b''
                
            return data
        except Exception as e:
            logger.error(f"Error reading from ffmpeg process: {str(e)}")
            self.cleanup()
            return b''

    def cleanup(self):
        """Clean up resources when done"""
        try:
            if self.process:
                try:
                    self.process.kill()
                except Exception:
                    pass
                self.process = None
                self.stdout = None
        except Exception as e:
            logger.error(f"Error cleaning up ffmpeg process: {str(e)}")

    def is_opus(self):
        return False
        
class YoutubeMusic(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.thread_pool = ThreadPoolExecutor(max_workers=2)
        self.currently_playing = {}  # Guild ID -> song info
        self.temp_dir = tempfile.mkdtemp(prefix="sezar_music_")
        
        # Server-optimized formats to reduce bandwidth and CPU usage
        self.optimized_format = 'bestaudio[ext=webm]/bestaudio[ext=m4a]/bestaudio'
        
        logger.info(f"YoutubeMusic cog initialized")
        logger.info(f"Temp directory created at: {self.temp_dir}")
        logger.info(f"Using ffmpeg-python library for audio processing")
    
    def cog_unload(self):
        """Clean up resources when cog is unloaded"""
        try:
            self.thread_pool.shutdown(wait=False)
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir, ignore_errors=True)
                logger.info(f"Removed temporary directory: {self.temp_dir}")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

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
                # Clean up resources for this guild
                if ctx.guild.id in self.currently_playing:
                    del self.currently_playing[ctx.guild.id]
                
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

    async def _get_song_info(self, url, search=False):
        """Get song info from YouTube in a thread to avoid blocking"""
        if search and not url.startswith(('https://', 'http://')):
            url = f"ytsearch:{url}"
        
        ydl_opts = {
            'format': self.optimized_format,
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'auto',
            'source_address': '0.0.0.0',
            # WispByte server optimization - reduce memory usage
            'geo_bypass': True,
            'nocheckcertificate': True,
            'ignoreerrors': True,
            'logtostderr': False,
            'cachedir': self.temp_dir,
            'extractor_retries': 3,
        }
        
        loop = asyncio.get_event_loop()
        try:
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                # Run in executor to avoid blocking
                info = await loop.run_in_executor(
                    self.thread_pool, 
                    lambda: ydl.extract_info(url, download=False)
                )
                
            if info is None:
                return None
                
            # Handle playlists vs single videos
            if 'entries' in info:
                info = info['entries'][0]
                
            return info
        except Exception as e:
            logger.error(f"Error getting song info: {str(e)}")
            return None

    @commands.hybrid_command(name='play', description='Belirtilen YouTube videosunun sesini çalar.')
    async def play(self, ctx, *, url: str):
        # Check if the bot is in a voice channel
        try:
            if ctx.voice_client is None:
                if ctx.author.voice:
                    await ctx.author.voice.channel.connect()
                    logger.info(f"Bot joined voice channel for music: {ctx.author.voice.channel.name}")
                else:
                    logger.warning(f"Play failed: User {ctx.author} not in a voice channel")
                    await ctx.reply("Lütfen önce bir ses kanalına katılın.")
                    return
            
            await ctx.defer()  # Let Discord know this might take a while
            logger.info(f"Music playback requested by {ctx.author}: {url}")
            
            # Get video info
            info = await self._get_song_info(url, search=True)
            if info is None:
                await ctx.reply("❌ Video bilgisi alınamadı. Lütfen başka bir video deneyin.")
                return
                
            audio_url = info['url']
            title = info.get('title', 'Bilinmeyen Şarkı')
            thumbnail = info.get('thumbnail')
            duration = info.get('duration', 0)  # Duration in seconds
            
            # Save current song info
            self.currently_playing[ctx.guild.id] = {
                'title': title,
                'url': audio_url,
                'thumbnail': thumbnail,
                'requester': ctx.author.name,
                'start_time': time.time(),
                'duration': duration
            }
            
            # Stop current audio if any
            if ctx.voice_client.is_playing():
                ctx.voice_client.stop()
                
            # Set audio options
            # Optimized for better performance
            FFMPEG_OPTIONS = {
                'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -nostdin',
                'options': '-vn -b:a 64k',  # Reduced bitrate for better performance
            }
            
            # Play the audio
            try:
                # Use our custom FFmpegPCMAudio that relies on ffmpeg-python
                source = FFmpegPCMAudio(
                    audio_url,
                    before_options=FFMPEG_OPTIONS.get('before_options', ''),
                    options=FFMPEG_OPTIONS.get('options', '')
                )
                
                # Add volume transformation with reduced volume to save resources
                source = discord.PCMVolumeTransformer(source, volume=0.5)
                ctx.voice_client.play(source)
                logger.info(f"Now playing: {title}")
                
                # Format duration
                if duration > 0:
                    minutes, seconds = divmod(duration, 60)
                    duration_str = f"{minutes}:{seconds:02d}"
                else:
                    duration_str = "Bilinmiyor"
                
                # Create embed with more info
                embed = discord.Embed(
                    title="🎵 Şu an çalınıyor",
                    description=f"**{title}**",
                    color=discord.Color.green()
                )
                
                embed.add_field(name="İsteyen", value=ctx.author.mention, inline=True)
                embed.add_field(name="Süre", value=duration_str, inline=True)
                
                if thumbnail:
                    embed.set_thumbnail(url=thumbnail)
                
                await ctx.reply(embed=embed)
                
            except Exception as e:
                logger.error(f"Error playing audio: {str(e)}")
                await ctx.reply(f"❌ Ses çalınırken bir hata oluştu: {str(e)}")
                
        except youtube_dl.utils.DownloadError as e:
            logger.error(f"YouTube download error: {str(e)}")
            await ctx.reply(f"❌ Video bulunamadı veya yüklenemedi. Lütfen başka bir şarkı deneyin.")
        except Exception as e:
            logger.error(f"General error in play command: {str(e)}")
            print(f"❌ Play komutunda genel hata: {str(e)}")
            await ctx.reply(f"❌ Komut işlenirken bir hata oluştu.")

    @commands.hybrid_command(name='nowplaying', description='Şu an çalan şarkının bilgilerini gösterir.')
    async def now_playing(self, ctx):
        """Shows information about the current song"""
        try:
            if not ctx.voice_client or not ctx.voice_client.is_playing():
                await ctx.reply("Şu anda çalan bir şarkı yok.")
                return
                
            guild_id = ctx.guild.id
            if guild_id not in self.currently_playing:
                await ctx.reply("Şarkı bilgisi bulunamadı.")
                return
                
            song_info = self.currently_playing[guild_id]
            
            # Calculate elapsed time
            elapsed = time.time() - song_info['start_time']
            elapsed_min, elapsed_sec = divmod(int(elapsed), 60)
            
            # Format total duration
            if song_info['duration'] > 0:
                total_min, total_sec = divmod(song_info['duration'], 60)
                duration_str = f"{elapsed_min}:{elapsed_sec:02d}/{total_min}:{total_sec:02d}"
            else:
                duration_str = f"{elapsed_min}:{elapsed_sec:02d}/??:??"
                
            # Create embed
            embed = discord.Embed(
                title="🎵 Şu an çalınıyor",
                description=f"**{song_info['title']}**",
                color=discord.Color.blue()
            )
            
            embed.add_field(name="İsteyen", value=song_info['requester'], inline=True)
            embed.add_field(name="Süre", value=duration_str, inline=True)
            
            if song_info['thumbnail']:
                embed.set_thumbnail(url=song_info['thumbnail'])
                
            await ctx.reply(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in nowplaying command: {str(e)}")
            await ctx.reply(f"❌ Şarkı bilgisi alınırken bir hata oluştu.")

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
                # Clear current song info
                if ctx.guild.id in self.currently_playing:
                    del self.currently_playing[ctx.guild.id]
                    
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

    @commands.hybrid_command(name='ffmpeg_check', description='FFmpeg kütüphane durumunu kontrol eder')
    async def ffmpeg_check(self, ctx):
        """Checks if ffmpeg-python is properly installed and configured"""
        try:
            # Try to create a simple ffmpeg input to check if the library is working
            try:
                # Create a test input
                test_input = ffmpeg.input('nullsrc', f='lavfi', t=0.1)
                version_info = "ffmpeg-python library: Available"
                
                embed = discord.Embed(
                    title="✅ FFmpeg Kütüphanesi Kontrolü Başarılı",
                    description=f"ffmpeg-python kütüphanesi çalışıyor.\n```\n{version_info}\n```",
                    color=discord.Color.green()
                )

                embed.add_field(
                    name="FFmpeg Python Kütüphanesi",
                    value=f"Sürüm: {ffmpeg.__version__ if hasattr(ffmpeg, '__version__') else 'Unknown'}",
                    inline=False
                )
                
                # Check Python version
                embed.add_field(
                    name="Python Sürümü",
                    value=f"Python {sys.version.split(' ')[0]}",
                    inline=False
                )
                
                # Add info about our custom audio player
                embed.add_field(
                    name="Özel Ses Oynatıcı",
                    value="FFmpegPCMAudio sınıfı ffmpeg-python kütüphanesini kullanacak şekilde özelleştirildi.",
                    inline=False
                )
                
                await ctx.reply(embed=embed)
            except Exception as e:
                # Library is available but there's an issue
                await ctx.reply(f"❌ ffmpeg-python kütüphanesi yüklü ancak çalıştırılırken bir hata oluştu: {str(e)}")
        except ImportError:
            # Library is not available
            await ctx.reply("❌ ffmpeg-python kütüphanesi yüklü değil. 'pip install ffmpeg-python' komutu ile yükleyin.")
        except Exception as e:
            logger.error(f"Error checking ffmpeg: {str(e)}")
            print(f"❌ FFmpeg kontrol hatası: {str(e)}")
            await ctx.reply(f"❌ FFmpeg kontrolü sırasında hata oluştu: {str(e)}")

    @commands.hybrid_command(name='audio_info', description='Ses dosyası hakkında bilgi verir')
    async def audio_info(self, ctx, url: str = None):
        """Gets audio information using ffmpeg-python"""
        try:
            await ctx.defer()  # This might take some time
            
            # If no URL is provided, check if something is currently playing
            if url is None:
                if ctx.guild.id in self.currently_playing:
                    url = self.currently_playing[ctx.guild.id]['url']
                else:
                    await ctx.reply("Lütfen bir ses dosyası URL'si belirtin veya önce bir şarkı çalın.")
                    return
            
            # If it's not a direct audio URL, try to get it from YouTube
            if not url.startswith(('http://', 'https://')) or 'youtube.com' in url or 'youtu.be' in url:
                info = await self._get_song_info(url, search=True)
                if info is None:
                    await ctx.reply("❌ Video bilgisi alınamadı. Lütfen başka bir URL deneyin.")
                    return
                url = info['url']
                title = info.get('title', 'Bilinmeyen Ses')
            else:
                title = "Verilen Ses Dosyası"
                
            # Use ffmpeg-python to analyze the audio
            try:
                # Create a temporary file path for downloading
                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                    temp_path = temp_file.name
                
                # Download a small portion of the audio for analysis
                await ctx.typing()
                await ctx.send("🔍 Ses dosyası analiz ediliyor, lütfen bekleyin...")
                
                # Use ffmpeg-python to download and analyze
                try:
                    # Download just the first 10 seconds for analysis
                    process = (
                        ffmpeg
                        .input(url, ss=0, t=10)  # Start at 0, duration 10 seconds
                        .output(temp_path)
                        .overwrite_output()
                        .run_async()
                    )
                    
                    # Wait for process to complete with timeout
                    try:
                        await asyncio.wait_for(
                            asyncio.to_thread(process.wait), 
                            timeout=30
                        )
                    except asyncio.TimeoutError:
                        process.kill()
                        await ctx.reply("❌ Analiz işlemi zaman aşımına uğradı.")
                        return
                    
                    # Analyze the downloaded segment
                    probe = ffmpeg.probe(temp_path)
                    
                    # Extract audio stream info
                    audio_streams = [stream for stream in probe['streams'] 
                                    if stream['codec_type'] == 'audio']
                    
                    if not audio_streams:
                        await ctx.reply("❌ Bu URL'de ses akışı bulunamadı.")
                        return
                        
                    # Get info from the first audio stream
                    audio = audio_streams[0]
                    
                    # Create embed with audio information
                    embed = discord.Embed(
                        title=f"🎵 Ses Dosyası Bilgileri: {title}",
                        color=discord.Color.blue()
                    )
                    
                    # Add codec info
                    embed.add_field(
                        name="Codec",
                        value=f"`{audio.get('codec_name', 'Bilinmiyor')}`",
                        inline=True
                    )
                    
                    # Add sample rate
                    embed.add_field(
                        name="Örnekleme Hızı",
                        value=f"{audio.get('sample_rate', 'Bilinmiyor')} Hz",
                        inline=True
                    )
                    
                    # Add channels info
                    channels = audio.get('channels', 0)
                    channel_layout = audio.get('channel_layout', 
                                             'mono' if channels == 1 else
                                             'stereo' if channels == 2 else
                                             f'{channels} kanal')
                    embed.add_field(
                        name="Kanal",
                        value=f"{channel_layout}",
                        inline=True
                    )
                    
                    # Add bit rate if available
                    if 'bit_rate' in audio:
                        bit_rate = int(audio['bit_rate']) / 1000
                        embed.add_field(
                            name="Bit Hızı",
                            value=f"{bit_rate:.1f} kbps",
                            inline=True
                        )
                    
                    # Add format info from probe
                    if 'format' in probe:
                        format_info = probe['format']
                        if 'format_name' in format_info:
                            embed.add_field(
                                name="Format",
                                value=format_info['format_name'],
                                inline=True
                            )
                    
                    await ctx.reply(embed=embed)
                    
                except ffmpeg.Error as e:
                    logger.error(f"FFmpeg error: {e.stderr.decode() if hasattr(e, 'stderr') else str(e)}")
                    await ctx.reply(f"❌ Ses analiz edilirken bir FFmpeg hatası oluştu.")
                finally:
                    # Clean up temp file
                    if os.path.exists(temp_path):
                        try:
                            os.unlink(temp_path)
                        except Exception:
                            pass
                    
            except Exception as e:
                logger.error(f"Error analyzing audio: {str(e)}")
                await ctx.reply(f"❌ Ses dosyası analiz edilirken bir hata oluştu: {str(e)}")
                
        except Exception as e:
            logger.error(f"General error in audio_info command: {str(e)}")
            await ctx.reply(f"❌ Komut işlenirken bir hata oluştu.")

async def setup(bot):
    try:
        await bot.add_cog(YoutubeMusic(bot))
        logger.info("YoutubeMusic cog loaded successfully")
        print("✅ Youtube Music modülü yüklendi")
    except Exception as e:
        logger.error(f"Failed to load YoutubeMusic cog: {str(e)}\n{traceback.format_exc()}")
        print(f"❌ Youtube Music modülü yüklenemedi: {str(e)}")
