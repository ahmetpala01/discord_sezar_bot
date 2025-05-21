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
        
        # Özel FFmpeg yolu - Kullanıcının kurduğu konum
        self.ffmpeg_path = r"C:\ffmpeg-master-latest-win64-gpl-shared\bin\ffmpeg.exe"
        
        # Eğer dosya yoksa sistem PATH'inden bulmaya çalış
        if not os.path.isfile(self.ffmpeg_path):
            self.ffmpeg_path = shutil.which('ffmpeg')
            
        print(f"FFmpeg yolu: {self.ffmpeg_path}")
        
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

    async def _search_youtube(self, query):
        """Doğrudan YouTube'da arama yapar ve ilk videoyu döndürür"""
        print(f"DEBUG: YouTube'da arama yapılıyor: {query}")
        
        # YouTube'un kendi arama sayfasına benzer bir URL oluştur
        # Bu, YouTube'un arama sonuçlarını doğrudan almak yerine
        # "YouTube'da <arama_terimi>" araması yapıp ilk sonucu alır
        direct_search_query = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,  # Tam video bilgisini al
            'default_search': 'auto',
            'source_address': '0.0.0.0',
            'geo_bypass': True,
            'nocheckcertificate': True,
        }
        
        try:
            # İki aşamalı yaklaşım: Önce arama sonuçlarını al, sonra ilk videonun bilgilerini al
                with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                # İlk olarak arama yap ve sonuçları al
                    print(f"DEBUG: Doğrudan YouTube arama URL'si: {direct_search_query}")
                try:
                    search_results = await self.bot.loop.run_in_executor(
                        self.thread_pool, 
                        lambda: ydl.extract_info(direct_search_query, download=False, process=False)
                    )
                    
                    if search_results is None or 'entries' not in search_results or not search_results['entries']:
                        print("DEBUG: Hiç arama sonucu bulunamadı")
                        return None
                        
                    # İlk videoyu al ve onun URL'sini kullan
                    first_result = search_results['entries'][0]
                    if 'url' not in first_result or not first_result['url'].startswith(('https://www.youtube.com', 'https://youtu.be')):
                        print(f"DEBUG: İlk sonuçta geçerli YouTube URL'si bulunamadı: {first_result.get('url', 'URL yok')}")
                    return None
                    
                    video_url = first_result['url']
                    print(f"DEBUG: İlk video URL'si: {video_url}")
                    
                    # Şimdi bu video URL'si için tam bilgileri al
                    video_info = await self.bot.loop.run_in_executor(
                        self.thread_pool,
                        lambda: ydl.extract_info(video_url, download=False, process=True)
                    )
                    
                    if video_info:
                        print(f"DEBUG: Video bilgisi alındı: {video_info.get('title', 'Başlık yok')}")
                        return video_info
                    else:
                        print("DEBUG: Video bilgisi alınamadı")
                        return None
                        
                except Exception as e:
                    print(f"DEBUG: YouTube arama hatası: {str(e)}")
                    # Yedek yöntem: Direkt YouTube linki oluşturmaya çalış
                    try:
                        # YouTube araması için URL oluştur
                        # Bu resmi olmayan bir yöntem ama denemeye değer
                        ytsearch_url = f"ytsearch:{query}"
                        print(f"DEBUG: Alternatif arama yöntemi deneniyor: {ytsearch_url}")
                        
                        search_results = await self.bot.loop.run_in_executor(
                            self.thread_pool,
                            lambda: ydl.extract_info(ytsearch_url, download=False)
                        )
                        
                        if search_results and 'entries' in search_results and search_results['entries']:
                            first_video = search_results['entries'][0]
                            print(f"DEBUG: Alternatif yöntem ile video bulundu: {first_video.get('title', 'Başlık yok')}")
                            return first_video
                            
                        print("DEBUG: Alternatif arama yöntemi de sonuç vermedi")
                        return None
                    except Exception as alt_e:
                        print(f"DEBUG: Alternatif arama yöntemi de başarısız oldu: {str(alt_e)}")
                        return None
                    
        except Exception as e:
            print(f"DEBUG: Arama işlemi sırasında genel hata: {str(e)}")
            return None
                
        return None

    async def _check_url_accessibility(self, link):
        """Check if a URL is accessible"""
        if not self.http_session:
            self.http_session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10),
                connector=aiohttp.TCPConnector(ssl=False)
            )
            
        try:
            async with self.http_session.head(link, timeout=5) as response:
                return response.status < 400
        except (ClientConnectorError, asyncio.TimeoutError, aiohttp.ClientError) as e:
            logger.warning(f"URL accessibility check failed for {link}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error checking URL accessibility: {str(e)}")
            return False

    @commands.hybrid_command(name='play', description='Belirtilen YouTube videosunun sesini çalar.')
    async def play(self, ctx, *, link: str):
        """Orijinal play komutu"""
        # Normal ses düzeyi ile çal (0.5 = 50%)
        await self._play_with_volume(ctx, link, volume=0.5)

    @commands.hybrid_command(
        name='çal',
        description='YouTube videosunun sesini çalar ve ses ayarlarını yapabilirsiniz'
    )
    @discord.app_commands.describe(
        link="YouTube video linki (search parametresi ile aynı anda kullanılamaz)",
        search="YouTubede aranacak şarkı/video adı (link parametresi ile aynı anda kullanılamaz)",
        ses="Ses düzeyi (20-1000 arası, varsayılan: 100)",
        bas="Bas miktarı (20-1000 arası, varsayılan: 100)",
        tizlik="Ses tonu ayarı (0-200 arası, 0: En kalın, 100: Normal, 200: En ince)",
        hız="Oynatma hızı (0.1-10 arası, varsayılan: 1 - normal hız)"
    )
    async def cal(
        self,
        ctx,
        link: str = None,
        search: str = None,
        ses: int = 100,
        bas: int = 100,
        tizlik: int = 100,
        hız: float = 1.0
    ):
        """
        YouTube videosunun sesini çalar, ses, bas ve tizlik düzeyini ayarlayabilirsiniz.
        
        Parametreler:
        - link: YouTube video linki (search ile aynı anda kullanılamaz)
        - search: YouTubede aranacak şarkı/video adı (link ile aynı anda kullanılamaz)
        - ses: Ses düzeyi (20-1000, varsayılan 100)
        - bas: Bas miktarı (20-1000, varsayılan 100)
        - tizlik: Ses tonu ayarı (0: En kalın, 100: Normal, 200: En ince)
        - hız: Oynatma hızı (0.1-10, varsayılan 1 - normal hız)
        """
        # Debug: Hangi parametrelerin geldiğini görelim
        print(f"DEBUG: çal komutu çağrıldı - link: {link}, search: {search}, ses: {ses}, bas: {bas}, tizlik: {tizlik}, hız: {hız}")
        
        # İnteraktif yanıt için kullanacağımız fonksiyon - ctx tipine göre uygun yanıt ver
        async def send_response(message, ephemeral=False):
            try:
                # Slash komut için followup kullan
                if hasattr(ctx, 'interaction') and ctx.interaction:
                    if hasattr(ctx, 'followup'):
                        await ctx.followup.send(message, ephemeral=ephemeral)
                    else:
                        await ctx.reply(message)
                else:
                    # Normal komut için reply kullan
                    await ctx.reply(message)
            except Exception as e:
                print(f"Yanıt gönderme hatası: {e}")
                try:
                    await ctx.channel.send(message)
                except:
                    print("Kanal mesajı da gönderilemedi")
        
        # İnteraktif komutsa defer et
        if hasattr(ctx, 'interaction') and ctx.interaction:
            try:
                await ctx.defer()
            except Exception as e:
                print(f"Defer hatası: {e}")
        
        # Link ve search parametrelerini kontrol et
        if link is None and search is None:
            await send_response("❌ Lütfen bir YouTube linki ya da arama terimi girin.")
            return
            
        if link is not None and search is not None:
            await send_response("❌ Aynı anda hem YouTube linki hem de arama terimi kullanamazsınız. Sadece birini belirtin.")
            return
            
        # Değerleri sınırlandır
        ses_duzeyi = max(20, min(1000, ses))
        bas_miktari = max(20, min(1000, bas))
        tizlik_miktari = max(0, min(200, tizlik))  # 0-200 arası sınırla
        hiz_miktari = max(0.1, min(10.0, hız))  # 0.1-10 arası sınırla
        
        # Değerler sınırlandırıldıysa bildir
        mesaj = ""
        if ses != ses_duzeyi:
            if ses < 20:
                mesaj += "⚠️ Ses düzeyi çok düşük! Minimum değer olan 20'ye ayarlandı.\n"
            else:
                mesaj += "⚠️ Ses düzeyi çok yüksek! Maksimum değer olan 1000'e ayarlandı.\n"
            
        if bas != bas_miktari:
            if bas < 20:
                mesaj += "⚠️ Bas miktarı çok düşük! Minimum değer olan 20'ye ayarlandı.\n"
            else:
                mesaj += "⚠️ Bas miktarı çok yüksek! Maksimum değer olan 1000'e ayarlandı.\n"
            
        if tizlik != tizlik_miktari:
            if tizlik < 0:
                mesaj += "⚠️ Tizlik miktarı çok düşük! Minimum değer olan 0'a ayarlandı.\n"
            else:
                mesaj += "⚠️ Tizlik miktarı çok yüksek! Maksimum değer olan 200'e ayarlandı.\n"
        
        if hız != hiz_miktari:
            if hız < 0.1:
                mesaj += "⚠️ Hız çok düşük! Minimum değer olan 0.1'e ayarlandı.\n"
            else:
                mesaj += "⚠️ Hız çok yüksek! Maksimum değer olan 10.0'a ayarlandı.\n"
        
        # Tizlik bilgisi ekle
        if tizlik_miktari < 100:
            kalinlik_yuzdesi = 100 - tizlik_miktari
            mesaj += f"🔊 Ses tonu: Kalın ses (-%{kalinlik_yuzdesi})\n"
        elif tizlik_miktari > 100:
            incelik_yuzdesi = tizlik_miktari - 100
            mesaj += f"🔊 Ses tonu: İnce ses (+%{incelik_yuzdesi})\n"
        else:
            mesaj += "🔊 Ses tonu: Normal\n"
        
        # Hız bilgisi ekle
        if hiz_miktari != 1.0:
            if hiz_miktari < 1.0:
                yavaslama_yuzdesi = round((1.0 - hiz_miktari) * 100)
                mesaj += f"⏱️ Oynatma hızı: Yavaşlatılmış (-%{yavaslama_yuzdesi})\n"
            else:
                hizlandirma_yuzdesi = round((hiz_miktari - 1.0) * 100)
                mesaj += f"⏱️ Oynatma hızı: Hızlandırılmış (+%{hizlandirma_yuzdesi})\n"
        else:
            mesaj += "⏱️ Oynatma hızı: Normal\n"
            
        # Ses ayarları hakkında bilgi
        mesaj += f"🔊 Ses düzeyi={ses_duzeyi}%, Bas miktarı={bas_miktari}%"
        
        # İlk bilgiyi Discord kanalına gönder (interaction değil, kanal)
        if mesaj:
            await ctx.channel.send(mesaj, delete_after=10)
        
        try:
            # Ses düzeylerini Discord PCMVolumeTransformer'ın kullandığı 0-2.0 aralığına çevir
            normalized_volume = ses_duzeyi / 100
            
            # Video bilgisini al
            info = None
            
            if search is not None:
                # Arama terimi verilmişse, YouTube'da ara
                await send_response(f"🔍 **{search}** için YouTube'da arama yapılıyor...", True)
                info = await self._search_youtube(search)
                
                if info is None:
                    await send_response(f"❌ **{search}** için YouTube'da sonuç bulunamadı veya bir hata oluştu.")
                    return
            else:
                # Link verilmişse
                is_youtube_url = link.startswith(('https://www.youtube.com', 'https://youtu.be', 'http://www.youtube.com'))
                
                if is_youtube_url:
                    # YouTube linki doğrudan kullan
                    info = await self._get_song_info(link)
                else:
                    # YouTube linki değilse arama yap
                    await send_response(f"🔍 **{link}** için YouTube'da arama yapılıyor...", True)
                    info = await self._search_youtube(link)
                
                if info is None or info == "NOT_FOUND":
                    if is_youtube_url:
                        await send_response("❌ Bu video bulunamıyor veya oynatılamıyor. Lütfen başka bir video deneyin.")
                    else:
                        await send_response(f"❌ **{link}** için YouTube'da sonuç bulunamadı veya bir hata oluştu.")
                    return
            
            # Audio URL'sini bul
            audio_url = None
            
            # Önce direct_url kontrolü (özel alanımız)
            if 'direct_url' in info:
                audio_url = info['direct_url']
                print("DEBUG: direct_url kullanılıyor")
            # Sonra url kontrolü (standart alan)
            elif 'url' in info:
                audio_url = info['url']
                print("DEBUG: url alanı kullanılıyor")
            # Son olarak formatlardan URL çıkarma
            elif 'formats' in info and info['formats']:
                for format in info['formats']:
                    if format.get('acodec') != 'none' and 'url' in format:
                        audio_url = format['url']
                        print("DEBUG: format URL'si kullanılıyor")
                        break
            
            if not audio_url:
                await send_response("❌ Video ses URL'si alınamadı.")
                return
            
            print(f"DEBUG: Audio URL: {audio_url[:50]}...")
            
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
                'duration': duration,
                'volume': normalized_volume,  # Ses düzeyini ekle
                'speed': hiz_miktari  # Hız bilgisini ekle
            }
            
            # Stop current audio if any
            if ctx.voice_client and ctx.voice_client.is_playing():
                ctx.voice_client.stop()
                
            # Set audio options with improved settings for server environments
            base_options = '-vn'  # Sadece ses, video yok
            extra_options = ""
            
            # FFmpeg için filtre oluştur
            audio_filters = []
            
            # Bass değerine göre FFmpeg filtresi oluştur
            if bas_miktari != 100:
                # Normalize bas seviyesini 0.2 - 10 aralığına çevir (daha etkili bas efekti için)
                bass_gain = (bas_miktari / 100) * 2  # 0.4 - 20 aralığına çevir
                audio_filters.append(f"bass=g={bass_gain}:f=110:w=0.6")
                print(f"DEBUG: Bas filtresi oluşturuldu: bass=g={bass_gain}:f=110:w=0.6")
            
            # Tizlik değerine göre FFmpeg filtresi oluştur
            if tizlik_miktari != 100:
                # Tizlik ayarını uygula
                if tizlik_miktari < 100:
                    # Kalınlaştırma modu (0-100 arası)
                    # 100'e yaklaştıkça etki azalır, 0'a yaklaştıkça daha kalın olur
                    kalinlik_orani = (100 - tizlik_miktari) / 100  # 0-1 arası normalizasyon
                    
                    # Bas artır, tiz azalt - daha güçlü efekt
                    bass_boost = 6 + (kalinlik_orani * 14)  # 6-20 dB arasında bas artışı
                    treble_cut = -10 * kalinlik_orani  # 0 ile -10 dB arasında tiz azaltma
                    mid_cut = -5 * kalinlik_orani  # Orta frekansları azalt
                    
                    # Ekolayzer ile farklı frekans bandlarını ayarla
                    audio_filters.append(f"equalizer=f=60:width_type=o:width=2:g={bass_boost}")  # Düşük frekansları artır
                    audio_filters.append(f"equalizer=f=300:width_type=o:width=1:g={mid_cut}")   # Orta frekansları azalt
                    audio_filters.append(f"equalizer=f=1000:width_type=o:width=1:g={mid_cut}")  # Orta frekansları azalt
                    audio_filters.append(f"equalizer=f=8000:width_type=o:width=2:g={treble_cut}")  # Yüksek frekansları azalt
                    
                    print(f"DEBUG: Kalınlaştırma efekti uygulandı (Bass +{bass_boost}dB, Mid {mid_cut}dB, Treble {treble_cut}dB)")
                    
                else:
                    # İnceleştirme modu (100-200 arası)
                    # 100'e yaklaştıkça etki azalır, 200'e yaklaştıkça daha ince olur
                    incelik_orani = (tizlik_miktari - 100) / 100  # 0-1 arası normalizasyon
                    
                    # Tiz artır, bas azalt - daha güçlü efekt
                    treble_boost = 6 + (incelik_orani * 14)  # 6-20 dB arasında tiz artışı
                    bass_cut = -10 * incelik_orani  # 0 ile -10 dB arasında bas azaltma
                    mid_boost = 3 * incelik_orani  # Orta frekansları artır
                    
                    # Ekolayzer ile farklı frekans bandlarını ayarla
                    audio_filters.append(f"equalizer=f=8000:width_type=o:width=2:g={treble_boost}")  # Yüksek frekansları artır
                    audio_filters.append(f"equalizer=f=3000:width_type=o:width=1:g={mid_boost}")  # Orta-yüksek frekansları artır
                    audio_filters.append(f"equalizer=f=1000:width_type=o:width=1:g={mid_boost}")  # Orta frekansları artır
                    audio_filters.append(f"equalizer=f=80:width_type=o:width=2:g={bass_cut}")  # Düşük frekansları azalt
                    
                    print(f"DEBUG: İnceleştirme efekti uygulandı (Treble +{treble_boost}dB, Mid +{mid_boost}dB, Bass {bass_cut}dB)")
            
            # Hız değerine göre FFmpeg filtresi oluştur
            if hiz_miktari != 1.0:
                # FFmpeg'in atempo filtresi 0.5 ile 2.0 arasındaki değerleri destekler
                # Daha geniş aralık için birden fazla atempo filtresi arka arkaya kullanılır
                
                target_speed = hiz_miktari
                print(f"DEBUG: Hedef hız: {target_speed}")
                
                # Hız 0.5'ten küçük veya 2.0'dan büyükse birden fazla filtre uygula
                if 0.5 <= target_speed <= 2.0:
                    # Doğrudan tek filtre kullan
                    audio_filters.append(f"atempo={target_speed}")
                    print(f"DEBUG: Hız filtresi oluşturuldu: atempo={target_speed}")
                else:
                    # Birden fazla filtre için faktörlere ayır
                    remaining_speed = target_speed
                    while remaining_speed < 0.5:
                        audio_filters.append("atempo=0.5")
                        remaining_speed /= 0.5
                    
                    while remaining_speed > 2.0:
                        audio_filters.append("atempo=2.0")
                        remaining_speed /= 2.0
                    
                    # Son kalan faktörü ekle (0.5-2.0 aralığında)
                    if 0.5 <= remaining_speed <= 2.0 and remaining_speed != 1.0:
                        audio_filters.append(f"atempo={remaining_speed}")
                    
                    print(f"DEBUG: Çoklu hız filtresi oluşturuldu: {audio_filters}")
            
            # Filtreleri birleştir
            if audio_filters:
                extra_options = f'-af "{",".join(audio_filters)}"'
                print(f"DEBUG: FFmpeg filtresi: {extra_options}")
                
            options = f"{base_options} {extra_options}"
            print(f"DEBUG: FFmpeg seçenekleri: {options}")
            
            # Custom play with volume, bass, treble and speed
            await self._play_with_volume(ctx, audio_url, volume=normalized_volume, extra_options=options)
            
            # Şarkı başlatıldı mesajı
            speed_info = f" ({hiz_miktari}x hızında)" if hiz_miktari != 1.0 else ""
            await send_response(f"🎵 **{title}**{speed_info} çalınıyor!", True)
        except Exception as e:
            print(f"Çal komutu hatası: {e}")
            await send_response(f"❌ Müzik çalma hatası: {e}")

    async def _play_with_volume(self, ctx, audio_url: str, volume: float = 0.5, extra_options: str = ""):
        """Ses URL'sini verilen ayarlarla çalar"""
        # Debug: Link kontrolü
        print(f"DEBUG: _play_with_volume çağrıldı - volume: {volume}")
        print(f"DEBUG: Ekstra FFmpeg seçenekleri: {extra_options}")
        
        # Initial checks and setup
        try:
            # Check if FFmpeg is available
            if not os.path.isfile(self.ffmpeg_path):
                logger.error("FFmpeg not found, cannot play audio")
                embed = discord.Embed(
                    title="❌ FFmpeg Bulunamadı",
                    description="Müzik çalabilmek için FFmpeg'e ihtiyaç vardır.",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="FFmpeg Nasıl Kurulur?", 
                    value="1. [FFmpeg İndirme Sayfası](https://ffmpeg.org/download.html)'nı ziyaret edin\n"
                          "2. Bilgisayarınıza uygun sürümü indirin\n"
                          "3. `C:\\ffmpeg` klasörüne çıkarın\n"
                          "4. PATH değişkenine ekleyin\n"
                          "5. Botu yeniden başlatın",
                    inline=False
                )
                await ctx.reply(embed=embed)
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
                    
            # FFmpeg audio source and options
            ffmpeg_options = {
                'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                'options': extra_options,
            }
            
            print(f"DEBUG: Çalma hazırlığı: {audio_url[:50]}...")
            print(f"DEBUG: FFmpeg yolu: {self.ffmpeg_path}")
            print(f"DEBUG: FFmpeg seçenekleri: {ffmpeg_options}")
            
            # Play the audio with robust error handling
            try:
                # Create the audio source
                source = discord.FFmpegPCMAudio(
                    audio_url,
                    executable=self.ffmpeg_path,
                    before_options=ffmpeg_options['before_options'],
                    options=ffmpeg_options['options']
                )
                print("DEBUG: FFmpegPCMAudio kaynağı oluşturuldu")
                
                # Add volume transformation with custom level
                source = discord.PCMVolumeTransformer(source, volume=volume)
                print(f"DEBUG: PCMVolumeTransformer uygulandı, ses: {volume}")
                
                # Play audio with after callback for error handling
                def after_playing(error):
                    if error:
                        logger.error(f"Error after playing: {error}")
                        print(f"❌ Oynatma hatası: {error}")
                        
                print("DEBUG: Ses çalmaya başlıyor...")
                ctx.voice_client.play(source, after=after_playing)
                logger.info(f"Now playing at volume {volume*100:.0f}%")
                print(f"🎵 Şarkı başladı (Ses: {volume*100:.0f}%)")
                
            except Exception as e:
                logger.error(f"Error playing audio: {str(e)}")
                print(f"❌ Kaynak çalma hatası: {str(e)}")
                await ctx.followup.send(f"❌ Ses çalınırken bir hata oluştu: {str(e)}")
                
        except Exception as e:
            logger.error(f"General error in play command: {str(e)}\n{traceback.format_exc()}")
            print(f"❌ Play komutunda genel hata: {str(e)}")
            await ctx.followup.send(f"❌ Komut işlenirken bir hata oluştu: {str(e)}")

    @commands.hybrid_command(name='testmuzik', description='Müzik çalma özelliğini test eder.')
    async def test_music(self, ctx):
        """Müzik sistemini test eder ve sorunları gösterir."""
        # Test embed hazırla
        embed = discord.Embed(
            title="🔍 Müzik Sistemi Testi",
            description="Müzik sisteminin durumunu kontrol ediyorum...",
            color=discord.Color.blue()
        )
        test_message = await ctx.reply(embed=embed)
        
        # FFmpeg testi
        ffmpeg_ok = False
        try:
            if os.path.isfile(self.ffmpeg_path):
                ffmpeg_version = subprocess.check_output([self.ffmpeg_path, "-version"], stderr=subprocess.STDOUT, text=True)
                ffmpeg_ok = "ffmpeg version" in ffmpeg_version
                embed.add_field(
                    name="✅ FFmpeg Kontrolü",
                    value=f"FFmpeg bulundu! Yolu: `{self.ffmpeg_path}`"
                )
            else:
                ffmpeg_ok = False
                embed.add_field(
                    name="❌ FFmpeg Kontrolü",
                    value="FFmpeg bulunamadı. Lütfen FFmpeg'i kurun veya botu yeniden başlatın."
                )
        except Exception as e:
            logger.error(f"FFmpeg testi hatası: {str(e)}")
            ffmpeg_ok = False
            embed.add_field(
                name="❌ FFmpeg Kontrolü",
                value="FFmpeg testi sırasında bir hata oluştu. Lütfen log dosyasını kontrol edin."
            )
        
        if ffmpeg_ok:
            embed.add_field(
                name="✅ Müzik Sistemi",
                value="Müzik sistemi çalışıyor ve ses çalıyor!"
            )
        else:
            embed.add_field(
                name="❌ Müzik Sistemi",
                value="Müzik sistemi çalışmıyor veya ses çalımıyor. Lütfen sorunları gidermeye çalışın."
            )
        
        await test_message.edit(embed=embed)

    # Kullanıcı parametrelerini gösteren komut
    @commands.hybrid_command(
        name='müzikyardım',
        description='Müzik komutlarının kullanımını gösterir.'
    )
    async def music_help(self, ctx):
        """Müzik komutlarının kullanımını ve parametre aralıklarını gösterir."""
        embed = discord.Embed(
            title="🎵 Müzik Komutları Yardımı",
            description="Müzik komutlarının kullanımı ve desteklenen parametre aralıkları:",
            color=discord.Color.blue()
        )
        
        # Çal komutu için bilgiler
        embed.add_field(
            name="/çal",
            value="YouTube'dan müzik çalar, ses düzeyi, bas ve tizlik ayarlanabilir.",
            inline=False
        )
        
        # Parametreler tablosu
        embed.add_field(
            name="Parametreler",
            value="```\nlink:   YouTube video linki (search ile birlikte kullanılamaz)\nsearch: Aranacak şarkı/video adı (link ile birlikte kullanılamaz)\nses:    20-1000 arası değer (varsayılan: 100)\nbas:    20-1000 arası değer (varsayılan: 100)\ntizlik:  0-200 arası değer (varsayılan: 100)\n        0: En kalın ses, 100: Normal, 200: En ince ses\nhız:     0.1-10 arası değer (varsayılan: 1 - normal hız)\n```",
            inline=False
        )
        
        # Kullanım örnekleri
        embed.add_field(
            name="Kullanım Örnekleri",
            value="```\n/çal link:https://www.youtube.com/watch?v=dQw4w9WgXcQ\n/çal search:Duman Seni Duman Etti\n/çal link:https://www.youtube.com/watch?v=dQw4w9WgXcQ ses:150 bas:200 tizlik:150 hız:1.5\n/çal search:Barış Manço Dağlar Dağlar tizlik:150 bas:120 hız:1.2\n```",
            inline=False
        )
        
        # Önerilen ayarlar
        embed.add_field(
            name="Önerilen Ayarlar",
            value="Normal ses: ses=100, bas=100, tizlik=100, hız=1.0\n"
                  "Çok kalın ses: ses=100, bas=150, tizlik=0, hız=0.5\n"
                  "Orta kalınlıkta: ses=100, bas=120, tizlik=50, hız=1.0\n"
                  "Orta incelikte: ses=100, bas=80, tizlik=150, hız=1.5\n"
                  "Çok ince ses: ses=100, bas=60, tizlik=200, hız=2.0\n"
                  "Bas ağırlıklı: ses=100, bas=300, tizlik=80, hız=1.0\n"
                  "Parti modu: ses=150, bas=200, tizlik=120, hız=1.2",
            inline=False
        )
        
        # Uyarılar
        embed.add_field(
            name="⚠️ Uyarılar",
            value="Çok yüksek ses değerleri (800-1000) ses kalitesinde bozulmaya neden olabilir.\n"
                  "Çok düşük (0) veya çok yüksek (200) tizlik değerleri bazı şarkılarda doğal olmayan sesler oluşturabilir.\n"
                  "En iyi sonuç için dengeli değerler kullanmanızı öneririz.",
            inline=False
        )
        
        await ctx.reply(embed=embed)

    @commands.hybrid_command(
        name='ez',
        description='Ses kanalındaki herkese özel bildirim gönderir.'
    )
    async def ez_command(self, ctx):
        """Ses kanalındaki tüm kullanıcılara bildirim gönderir."""
        # Komutu kullanan kişi ses kanalında mı kontrol et
        if not ctx.author.voice:
            await ctx.reply("❌ Bu komutu kullanmak için bir ses kanalında olmalısınız.")
            return
            
        # Kullanıcının bulunduğu ses kanalı
        voice_channel = ctx.author.voice.channel
        
        # Ses kanalındaki üye sayısı
        member_count = len(voice_channel.members)
        
        if member_count <= 1:
            await ctx.reply("⚠️ Ses kanalında sizden başka kimse yok.")
            return
        
        # Yeni bildirim mesajı (sesli okunacak)
        message = "🍈 Kafasını ezmek istiyorum. Sen istemiyor musun?"
        
        # Orijinal mesajı sil (yollayan gözükmesin diye)
        try:
            await ctx.message.delete()
        except:
            pass
            
        # Bildirim gönderildi bilgisi (sadece komutu çalıştıran kişiye özel mesaj olarak)
        try:
            await ctx.author.send(f"✅ Ses kanalındaki {member_count-1} kişiye bildirim gönderildi.")
        except:
            # DM kapalıysa kanala mesaj gönder ve hemen sil
            temp_msg = await ctx.channel.send(f"✅ Ses kanalındaki {member_count-1} kişiye bildirim gönderildi.")
            await asyncio.sleep(3)
            await temp_msg.delete()
        
        # DM Gönderme - Basitleştirilmiş mesaj
        # Ses kanalındaki her üyeye DM göndermeye çalış
        success_count = 0
        for member in voice_channel.members:
            # Kendine mesaj gönderme
            if member.id == ctx.author.id:
                continue
                
            try:
                # Basit davetiye mesajı
                simple_message = "Sende kavunun kafasını ezmek istiyorsan AhmetStudios'a katıl."
                
                # DM gönder
                await member.send(f"🍈 {simple_message}")
                success_count += 1
            except Exception as e:
                logger.error(f"DM gönderme hatası ({member.display_name}): {e}")
        
        # Başarılı DM gönderimini raporla (sildirilecek)
        if success_count > 0 and ctx.guild:
            temp_msg = await ctx.channel.send(f"✅ {success_count} kişiye özel mesaj gönderildi.", delete_after=5)
        
        # TTS ile Sesli Mesaj (etiketleme olmadan)
        try:
            # Sesli mesaj sadece kanalda gösterilecek
            tts_msg = await ctx.channel.send(message, tts=True)
            # 10 saniye sonra mesajı sil
            await asyncio.sleep(10)
            await tts_msg.delete()
        except Exception as e:
            logger.error(f"TTS gönderme hatası: {e}")
        
        # YouTube linkini otomatik çalma
        try:
            # YouTube linkini verilen parametrelerle çal
            # Async fonksiyon olduğu için context içinde çağrılması gerekiyor
            ctx.invoked_with = "çal"  # Komutu çal olarak tanımla
            ctx.command = self.bot.get_command("çal")  # çal komutunu al
            
            if ctx.command:
                # Çal komutunu yeni parameterlerle çağır
                await self.cal(
                    ctx, 
                    link="https://www.youtube.com/watch?v=VSi_-r3OuuE",
                    search=None,
                    ses=1000,
                    bas=300,
                    tizlik=200,
                    hız=1.5
                )
            else:
                logger.error("Çal komutu bulunamadı")
        except Exception as e:
            logger.error(f"Otomatik çalma hatası: {e}")
            print(f"Otomatik çalma hatası: {e}")

    async def _get_song_info(self, link, search=False):
        """Get song info from YouTube in a thread to avoid blocking"""
        print(f"DEBUG: Video bilgisi alınıyor: {link}")
        
        # YouTube linki kontrolü
        if not link.startswith(('https://www.youtube.com', 'https://youtu.be', 'http://www.youtube.com')):
            print(f"DEBUG: URL bir YouTube linki değil, arama yapılmayacak: {link}")
            return None
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'auto',
            'source_address': '0.0.0.0',
            'geo_bypass': True,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': True,
            'cachedir': False,
            'verbose': True,
        }
        
        loop = asyncio.get_event_loop()
        
        # Add retry mechanism
        for attempt in range(3):
            try:
                print(f"DEBUG: YT-DLP Deneme {attempt+1}/3")
                with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                    # Run in executor to avoid blocking
                    info = await loop.run_in_executor(
                        self.thread_pool, 
                        lambda: ydl.extract_info(link, download=False)
                    )
                    
                if info is None:
                    print(f"DEBUG: YT-DLP boş bilgi döndürdü")
                    logger.warning(f"No info returned from YouTube-DL for {link}")
                    if attempt < 2:
                        await asyncio.sleep(1)
                        continue
                    return None
                
                print(f"DEBUG: Video bilgisi alındı: {info.get('title', 'Başlık yok')}")
                return info
                
            except youtube_dl.utils.DownloadError as e:
                logger.error(f"YouTube-DL download error (attempt {attempt+1}/3): {str(e)}")
                print(f"DEBUG: YT-DLP indirme hatası: {str(e)}")
                
                # Check for "Video unavailable" or "no video results"
                if "Video unavailable" in str(e) or "no video results" in str(e) or "No video results" in str(e):
                    print(f"DEBUG: Video bulunamadı veya kullanılamıyor")
                    return "NOT_FOUND"
                    
                if attempt < 2:
                    await asyncio.sleep(1.5)
                    continue
                return None
            except Exception as e:
                logger.error(f"Error getting song info (attempt {attempt+1}/3): {str(e)}")
                print(f"DEBUG: Genel hata: {str(e)}")
                if attempt < 2:
                    await asyncio.sleep(1.5)
                    continue
                return None
                
        return None  # Return None if all attempts failed

async def setup(bot):
    await bot.add_cog(YoutubeMusic(bot))