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
from urllib.parse import urlparse
import aiohttp
from aiohttp.client_exceptions import ClientConnectorError

# Configure logger for this module
logger = logging.getLogger('sezar.music')

# Set up more detailed logging for debugging on the server
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    file_handler = logging.FileHandler('music.log')
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)

class FFmpegPCMAudio(discord.AudioSource):
    """Audio source for FFmpeg with enhanced error handling for server environments"""
    def __init__(self, source, *, executable=None, pipe=False, stderr=None, before_options=None, options=None):
        self.source = source
        self.pipe = pipe
        self.stderr = stderr
        self.before_options = before_options or ''
        self.options = options or ''
        self.process = None
        self.stdout = None
        self.block_size = 3840  # opus frame size * 2 channels * 2 bytes per sample
        
        # FFmpeg executable finding with better error handling
        if executable:
            self.executable = executable
        else:
            self.executable = self._find_ffmpeg()
            
        logger.debug(f"FFmpegPCMAudio initialized with executable: {self.executable}")
        logger.debug(f"Source: {source}")
        logger.debug(f"Before options: {before_options}")
        logger.debug(f"Options: {options}")

    def _find_ffmpeg(self):
        """Find FFmpeg executable with comprehensive search"""
        # Check environment variable first (for Docker/container setups)
        ffmpeg_path = os.environ.get('FFMPEG_PATH')
        if ffmpeg_path and os.path.isfile(ffmpeg_path):
            logger.info(f"Using FFmpeg from environment variable: {ffmpeg_path}")
            return ffmpeg_path
            
        # Check if ffmpeg is in system PATH
        ffmpeg_in_path = shutil.which('ffmpeg')
        if ffmpeg_in_path:
            logger.info(f"Found FFmpeg in system PATH: {ffmpeg_in_path}")
            return ffmpeg_in_path
            
        # Check common locations based on OS
        if platform.system() == 'Windows':
            common_paths = [
                r'C:\ffmpeg\bin\ffmpeg.exe',
                r'C:\Program Files\ffmpeg\bin\ffmpeg.exe',
                r'C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe',
            ]
        else:  # Linux/Mac
            common_paths = [
                '/usr/bin/ffmpeg',
                '/usr/local/bin/ffmpeg',
                '/opt/ffmpeg/bin/ffmpeg',
                '/app/ffmpeg'  # Common Docker location
            ]
            
        for path in common_paths:
            if os.path.isfile(path):
                logger.info(f"Found FFmpeg at: {path}")
                return path
                
        # Last resort - try using just 'ffmpeg' and hope it works
        logger.warning("FFmpeg not found in any expected location, falling back to 'ffmpeg'")
        return 'ffmpeg'

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
            
            # Create the process with more robust error handling
            try:
                self.process = subprocess.Popen(
                    args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE if not self.pipe else subprocess.STDOUT,
                    bufsize=self.block_size  # Buffering helps with smoother playback
                )
                
                if self.process.poll() is not None:
                    # Process ended immediately - probably an error
                    raise Exception(f"FFmpeg process failed to start! Exit code: {self.process.returncode}")
                
                self.stdout = self.process.stdout
                
            except FileNotFoundError:
                logger.error(f"FFmpeg executable not found: {self.executable}")
                raise
                
        except Exception as e:
            error_message = str(e)
            stderr_output = ""
            
            # Try to get stderr output if available
            if self.process and hasattr(self.process, 'stderr') and self.process.stderr:
                try:
                    stderr_output = self.process.stderr.read().decode('utf-8', errors='replace')
                except:
                    pass
                
            if stderr_output:
                logger.error(f"FFmpeg error: {error_message}\nFFmpeg stderr: {stderr_output}")
            else:
                logger.error(f"Error creating FFmpeg process: {error_message}")
                
            # Clean up if needed
            if self.process:
                try:
                    self.process.kill()
                except:
                    pass
                    
            raise

    def read(self):
        if self.process is None:
            try:
                self._create_process()
            except Exception as e:
                logger.error(f"Failed to create FFmpeg process: {e}")
                return b''  # Return empty to indicate end of stream

        try:
            # Read bytes from stdout of the ffmpeg process
            data = self.stdout.read(self.block_size)
            
            if not data:
                # End of the stream
                self.cleanup()
                return b''
                
            return data
        except Exception as e:
            logger.error(f"Error reading from FFmpeg process: {str(e)}")
            self.cleanup()
            return b''

    def cleanup(self):
        """Clean up resources when done"""
        try:
            if self.process:
                try:
                    self.process.kill()
                except Exception as e:
                    logger.debug(f"Error killing process during cleanup: {e}")
                self.process = None
                self.stdout = None
        except Exception as e:
            logger.error(f"Error cleaning up FFmpeg process: {str(e)}")

    def is_opus(self):
        return False
        
class YoutubeMusic(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.thread_pool = ThreadPoolExecutor(max_workers=3)  # Increased for better performance
        self.currently_playing = {}  # Guild ID -> song info
        self.temp_dir = tempfile.mkdtemp(prefix="sezar_music_")
        self.http_session = None  # Will be initialized in cog_load
        
        # Use environment variable for FFmpeg if available
        self.ffmpeg_path = os.environ.get('FFMPEG_PATH')
        
        # If not set in environment, try to find it
        if not self.ffmpeg_path or not os.path.isfile(self.ffmpeg_path):
            self.ffmpeg_path = self._find_ffmpeg()
        
        # Format selection - optimize for server performance
        self.optimized_format = 'bestaudio[ext=webm]/bestaudio[ext=m4a]/bestaudio'
        
        logger.info(f"YoutubeMusic cog initialized")
        logger.info(f"Temp directory created at: {self.temp_dir}")
        logger.info(f"FFmpeg path: {self.ffmpeg_path}")
    
    def _find_ffmpeg(self):
        """Find FFmpeg executable with comprehensive search"""
        # Use the same FFmpeg finding logic as in FFmpegPCMAudio
        ffmpeg_path = shutil.which('ffmpeg')
        if ffmpeg_path:
            return ffmpeg_path
            
        # Check common locations based on OS
        if platform.system() == 'Windows':
            common_paths = [
                r'C:\ffmpeg\bin\ffmpeg.exe',
                r'C:\Program Files\ffmpeg\bin\ffmpeg.exe',
                r'C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe',
            ]
        else:  # Linux/Mac
            common_paths = [
                '/usr/bin/ffmpeg',
                '/usr/local/bin/ffmpeg',
                '/opt/ffmpeg/bin/ffmpeg',
                '/app/ffmpeg'  # Common Docker location
            ]
            
        for path in common_paths:
            if os.path.isfile(path):
                return path
                
        return 'ffmpeg'  # Default fallback
    
    async def cog_load(self):
        """Setup resources when cog is loaded"""
        # Create HTTP session for URL checks
        self.http_session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10),
            connector=aiohttp.TCPConnector(ssl=False)  # Disable SSL for better compatibility
        )
    
    async def cog_unload(self):
        """Clean up resources when cog is unloaded"""
        try:
            # Close HTTP session if it exists
            if self.http_session:
                await self.http_session.close()
                
            # Shutdown thread pool
            self.thread_pool.shutdown(wait=False)
            
            # Remove temp directory
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
                    
                # Connect with timeout and better error handling
                try:
                    await channel.connect(timeout=15.0, reconnect=True)
                    logger.info(f"Bot joined voice channel: {channel.name}")
                    await ctx.reply("Ses kanalına bağlandım.")
                except asyncio.TimeoutError:
                    logger.error(f"Timeout connecting to voice channel {channel.name}")
                    await ctx.reply("⚠️ Ses kanalına bağlanırken zaman aşımı oluştu. Lütfen tekrar deneyin.")
                except Exception as e:
                    logger.error(f"Error connecting to voice channel: {str(e)}")
                    await ctx.reply(f"⚠️ Ses kanalına bağlanırken bir hata oluştu: {str(e)}")
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
                await ctx.voice_client.disconnect(force=True)  # Force disconnect in case of issues
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
            # Server optimization options
            'geo_bypass': True,
            'nocheckcertificate': True,
            'ignoreerrors': True,
            'logtostderr': False,
            'cachedir': self.temp_dir,
            'extractor_retries': 3,
            'retries': 5,
            'fragment_retries': 5,
            'skip_download': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        }
        
        loop = asyncio.get_event_loop()
        
        # Add retry mechanism
        for attempt in range(3):
            try:
                with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                    # Run in executor to avoid blocking
                    info = await loop.run_in_executor(
                        self.thread_pool, 
                        lambda: ydl.extract_info(url, download=False)
                    )
                    
                if info is None:
                    logger.warning(f"No info returned from YouTube-DL for {url}")
                    if attempt < 2:
                        await asyncio.sleep(1)
                        continue
                    return None
                    
                # Handle playlists vs single videos
                if 'entries' in info:
                    if not info['entries']:
                        logger.warning(f"Empty entries list returned from YouTube-DL for {url}")
                        if attempt < 2:
                            await asyncio.sleep(1)
                            continue
                        return None
                    info = info['entries'][0]
                    
                return info
            except youtube_dl.utils.DownloadError as e:
                logger.error(f"YouTube-DL download error (attempt {attempt+1}/3): {str(e)}")
                if attempt < 2:
                    await asyncio.sleep(1.5)
                    continue
                return None
            except Exception as e:
                logger.error(f"Error getting song info (attempt {attempt+1}/3): {str(e)}")
                if attempt < 2:
                    await asyncio.sleep(1.5)
                    continue
                return None
                
        return None  # Return None if all attempts failed

    async def _check_url_accessibility(self, url):
        """Check if a URL is accessible"""
        if not self.http_session:
            self.http_session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10),
                connector=aiohttp.TCPConnector(ssl=False)
            )
            
        try:
            async with self.http_session.head(url, timeout=5) as response:
                return response.status < 400
        except (ClientConnectorError, asyncio.TimeoutError, aiohttp.ClientError) as e:
            logger.warning(f"URL accessibility check failed for {url}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error checking URL accessibility: {str(e)}")
            return False

    @commands.hybrid_command(name='play', description='Belirtilen YouTube videosunun sesini çalar.')
    async def play(self, ctx, *, url: str):
        # Initial checks and setup
        try:
            # Check if FFmpeg is available
            if not self.ffmpeg_path:
                logger.error("FFmpeg not found, cannot play audio")
                await ctx.reply("❌ FFmpeg bulunamadı. Müzik çalınamıyor.")
                return
                
            # Check if the bot is in a voice channel
            if ctx.voice_client is None:
                if ctx.author.voice:
                    try:
                        await ctx.author.voice.channel.connect(timeout=15.0, reconnect=True)
                        logger.info(f"Bot joined voice channel for music: {ctx.author.voice.channel.name}")
                    except asyncio.TimeoutError:
                        logger.error(f"Timeout connecting to voice channel")
                        await ctx.reply("⚠️ Ses kanalına bağlanırken zaman aşımı oluştu. Lütfen tekrar deneyin.")
                        return
                    except Exception as e:
                        logger.error(f"Error connecting to voice channel: {str(e)}")
                        await ctx.reply(f"⚠️ Ses kanalına bağlanırken bir hata oluştu: {str(e)}")
                        return
                else:
                    logger.warning(f"Play failed: User {ctx.author} not in a voice channel")
                    await ctx.reply("Lütfen önce bir ses kanalına katılın.")
                    return
                    
            # Let Discord know this might take a while
            await ctx.defer()
            logger.info(f"Music playback requested by {ctx.author}: {url}")
            
            # Get video info with retries
            info = await self._get_song_info(url, search=True)
            if info is None:
                await ctx.reply("❌ Video bilgisi alınamadı. Lütfen başka bir video deneyin.")
                return
                
            audio_url = info['url']
            title = info.get('title', 'Bilinmeyen Şarkı')
            thumbnail = info.get('thumbnail')
            duration = info.get('duration', 0)  # Duration in seconds
            
            # Test URL accessibility
            if not await self._check_url_accessibility(audio_url):
                # Try alternative formats if main URL is inaccessible
                logger.warning(f"Main audio URL is not accessible: {audio_url}")
                
                alt_formats = info.get('formats', [])
                accessible_url = None
                
                for fmt in alt_formats:
                    if fmt.get('acodec') != 'none' and fmt.get('url'):
                        alt_url = fmt.get('url')
                        if await self._check_url_accessibility(alt_url):
                            accessible_url = alt_url
                            logger.info(f"Found accessible alternative URL")
                            break
                            
                if accessible_url:
                    audio_url = accessible_url
                else:
                    logger.error("No accessible audio URL found")
                    await ctx.reply("❌ Ses kaynağına erişilemiyor. Lütfen başka bir video deneyin.")
                    return
            
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
                
            # Set audio options with improved settings for server environments
            FFMPEG_OPTIONS = {
                'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -nostdin -analyzeduration 0 -loglevel 0',
                'options': '-vn -b:a 96k -bufsize 8192k -thread_queue_size 4096',
            }
            
            # Play the audio with robust error handling
            try:
                # Create FFmpegPCMAudio source with our optimized settings
                source = FFmpegPCMAudio(
                    audio_url,
                    executable=self.ffmpeg_path,
                    before_options=FFMPEG_OPTIONS.get('before_options', ''),
                    options=FFMPEG_OPTIONS.get('options', '')
                )
                
                # Add volume transformation
                source = discord.PCMVolumeTransformer(source, volume=0.5)
                
                # Play audio with after callback for error handling
                def after_playing(error):
                    if error:
                        logger.error(f"Error after playing: {error}")
                        
                ctx.voice_client.play(source, after=after_playing)
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
            logger.error(f"General error in play command: {str(e)}\n{traceback.format_exc()}")
            print(f"❌ Play komutunda genel hata: {str(e)}")
            await ctx.reply(f"❌ Komut işlenirken bir hata oluştu. Detaylar için sunucu loglarını kontrol edin.")

async def setup(bot):
    await bot.add_cog(YoutubeMusic(bot))
