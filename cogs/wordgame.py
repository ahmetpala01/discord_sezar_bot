from discord.ext import commands
import re
import logging
import traceback
import sys

# Configure logger for this module
logger = logging.getLogger('sezar.wordgame')

class WordGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.game_channel = None
        self.last_word = None
        self.word_list = self.load_word_list()
        logger.info("WordGame cog initialized")

    def load_word_list(self):
        """words.txt dosyasından Türkçe kelime listesini yükler."""
        try:
            with open('words.txt', 'r', encoding='utf-8') as file:
                word_list = set(word.strip().lower() for word in file)
                logger.info(f"Word list loaded with {len(word_list)} words")
                return word_list
        except FileNotFoundError:
            logger.error("words.txt file not found!")
            print("❌ words.txt bulunamadı!")
            return set()
        except Exception as e:
            logger.error(f"Error loading words.txt: {str(e)}")
            print(f"❌ Kelime listesi yüklenirken hata oluştu: {str(e)}")
            return set()

    def is_turkish_word(self, word):
        """Kelimenin Türkçe olup olmadığını kontrol eder."""
        word = word.lower()
        # Uzun ünlüler (â, î, û) kontrolü - genellikle ödünç kelimelerde bulunur
        if any(char in word for char in 'âîû'):
            return False
        # Kelime listesinde var mı?
        if word not in self.word_list:
            return False
        # İlk hece dışındaki hecelerde o, ö kontrolü
        syllables = self.get_syllables(word)
        for syllable in syllables[1:]:  # İlk heceyi atla
            if 'o' in syllable or 'ö' in syllable:
                return False
        return True

    def get_syllables(self, word):
        """Kelimeyi hecelere ayırır."""
        vowels = 'aeıioöuü'
        syllables = []
        current_syllable = ""
        for char in word:
            current_syllable += char
            if char in vowels:
                syllables.append(current_syllable)
                current_syllable = ""
        if current_syllable:
            syllables[-1] += current_syllable
        return syllables

    def is_valid_word(self, word, last_word):
        """Kelimenin oyun kurallarına uygun olup olmadığını kontrol eder."""
        word = word.lower()
        # Türkçe kelime mi?
        if not self.is_turkish_word(word):
            return False, "Bu kelime Türkçe değil veya kurallara uymuyor (örneğin, ilk hece dışında 'o' veya 'ö' içeriyor veya uzun ünlüler içeriyor)."
        # Son harf kuralı
        if last_word and word[0] != last_word[-1]:
            return False, f"Kelime, önceki kelimenin son harfi '{last_word[-1]}' ile başlamalı."
        # Sadece harflerden oluşmalı
        if not re.match(r'^[a-zçğışöü]+$', word):
            return False, "Kelime sadece Türkçe harfler içermeli."
        return True, ""

    @commands.command(name='kelimeoyunu')
    async def start_game(self, ctx):
        """Kelime oyununu başlatır."""
        try:
            if self.game_channel:
                await ctx.send("Oyun zaten bir kanalda aktif!")
                logger.info(f"Game start attempt rejected - already active in {self.game_channel.name}")
                return
                
            self.game_channel = ctx.channel
            self.last_word = None
            await ctx.send("Kelime oyunu başladı! İlk Türkçe kelimeyi yazın. Kurallar: "
                        "1) Kelime Türkçe olmalı, "
                        "2) İlk hece dışında 'o' veya 'ö' içermemeli, "
                        "3) Uzun ünlüler (â, î, û) içermemeli, "
                        "4) Bir önceki kelimenin son harfiyle başlamalı.")
            logger.info(f"Word game started in channel: {ctx.channel.name} by {ctx.author}")
        except Exception as e:
            logger.error(f"Error starting word game: {str(e)}")
            print(f"❌ Kelime oyunu başlatılırken hata: {str(e)}")
            await ctx.send("Oyun başlatılırken bir hata oluştu.")

    @commands.command(name='bitir')
    async def end_game(self, ctx):
        """Kelime oyununu sonlandırır."""
        try:
            if self.game_channel != ctx.channel:
                await ctx.send("Oyun bu kanalda aktif değil!")
                return
                
            self.game_channel = None
            self.last_word = None
            await ctx.send("Oyun sona erdi!")
            logger.info(f"Word game ended in channel: {ctx.channel.name} by {ctx.author}")
        except Exception as e:
            logger.error(f"Error ending word game: {str(e)}")
            print(f"❌ Kelime oyunu sonlandırılırken hata: {str(e)}")
            await ctx.send("Oyun sonlandırılırken bir hata oluştu.")

    @commands.Cog.listener()
    async def on_message(self, message):
        """Mesajları dinler ve oyun kanalında kelime kontrolü yapar."""
        if message.author.bot or self.game_channel != message.channel:
            return
        
        try:
            word = message.content.strip().lower()
            is_valid, error = self.is_valid_word(word, self.last_word)
            
            if is_valid:
                self.last_word = word
                await message.add_reaction('✅')
                logger.debug(f"Valid word: '{word}' from {message.author}")
            else:
                await message.add_reaction('❌')
                await message.channel.send(f"Geçersiz kelime: {error}")
                logger.debug(f"Invalid word: '{word}' from {message.author} - Reason: {error}")
                
            await self.bot.process_commands(message)
        except Exception as e:
            logger.error(f"Error processing word: {str(e)}")
            print(f"❌ Kelime kontrolü yapılırken hata: {str(e)}")

async def setup(bot):
    await bot.add_cog(WordGame(bot))
