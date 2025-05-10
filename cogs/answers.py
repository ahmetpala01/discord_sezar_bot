import os
import discord
import random
import re
from discord.ext import commands

class Answer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.responses = [
            "Kesinlikle katılıyorum!",
            "Bence haklı değilsiniz.",
            "Belki de öyledir.",
            "Bilmiyorum, ama denemeye değer olabilir.",
            "Bu konuyu düşünmem gerekiyor.",
            "Bunu yapmayı düşünebilirsiniz.",
            "Bunu yapmak istemeyebilirsiniz.",
            "Öyle düşünmüyorum.",
            "Evet, bence denemelisiniz!",
        ]
        
        # Greetings and casual chat responses
        self.greetings = {
            r"merhaba|selam|hey|hi|hello|sa|sea|selamün aleyküm|selamun aleykum": [
                "Aleykümselam!",
                "Merhaba! Nasılsınız?",
                "Hoş geldiniz!",
                "Merhaba! Nasıl yardımcı olabilirim?",
                "Selamlar! Bugün size nasıl yardım edebilirim?",
                "Merhaba! Ne yapıyorsunuz?",
            ],
            r"nasılsın|naber|ne haber": [
                "İyiyim, teşekkür ederim, sizi sormalı?",
                "İyiyim, teşekkürler! Siz nasılsınız?",
                "Gayet iyiyim! Siz nasılsınız?",
                "Bir bot olarak her zamanki gibiyim. Siz nasılsınız?",
                "Hizmetinizdeyim, her şey yolunda!",
            ],
            r"teşekkür|teşekkürler|sağol": [
                "Rica ederim!",
                "Ne demek, her zaman!",
                "Yardımcı olabildiysem ne mutlu bana!",
                "Bir şey değil, başka bir konuda yardıma ihtiyacınız olursa buradayım.",
            ]
        }
        
        # Different categories of questions with specific answers
        self.categorized_answers = {
            "time": [
                "Şu anki saate göre...",
                "Zamanı geldiğinde göreceğiz!",
                "Zamanın her şeyi göstereceğine inanıyorum.",
            ],
            "decision": [
                "Bu sizin kararınız olmalı, ama denemeyi düşünebilirsiniz.",
                "Bunu yapmak istediğinize gerçekten emin misiniz?",
                "Eğer gerçekten istiyorsanız yapmalısınız!",
                "Bazen beklemek en iyisidir.",
            ],
            "prediction": [
                "Geleceği görebilseydim size söylerdim!",
                "Büyük ihtimalle evet!",
                "Sanırım bu gerçekleşmeyecek.",
                "Olasılıklar olumlu görünüyor!",
            ],
            "identity": [
                "Ben Discord Sezar Bot'um! Size yardımcı olmak için buradayım.",
                "Ben bir Discord yardım botuyum. Size nasıl yardımcı olabilirim?",
                "Ben Discord üzerinde çalışan bir sohbet ve yardım botuyum.",
                "Adım Sezar Bot! Sorularınızı cevaplamak ve yardımcı olmak için buradayım.",
            ]
        }

    @commands.hybrid_command(name="sorusor", description="Bir cevap istiyorsan alırsın")
    async def ask_question(self, ctx, *, question: str):
        # Categorize the question if possible
        if any(word in question.lower() for word in ["kimsin", "sen kimsin", "kendini tanıt", "bot musun", "nesin sen"]):
            response = random.choice(self.categorized_answers["identity"])
        elif any(word in question.lower() for word in ["ne zaman", "zaman", "süre", "saat"]):
            response = random.choice(self.categorized_answers["time"])
        elif any(word in question.lower() for word in ["yapmalı mıyım", "etmeli miyim", "karar", "seçmeli miyim"]):
            response = random.choice(self.categorized_answers["decision"])
        elif any(word in question.lower() for word in ["olacak mı", "gerçekleşecek mi", "başarılı olacak mıyım"]):
            response = random.choice(self.categorized_answers["prediction"])
        else:
            response = random.choice(self.responses)
            
        # Create a nice embed for the answer
        embed = discord.Embed(
            description=f"{question} \n Bu soruya cevabım: {response}",
            color=discord.Color.purple()
        )        
        await ctx.reply(embed=embed)
        
    @commands.hybrid_command(name="sohbet", description="Benimle sohbet et")
    async def chat(self, ctx, *, message: str):
        response = "Anlamadım, daha açık konuşabilir misiniz?"
        
        # Check for identity questions
        if any(word in message.lower() for word in ["kimsin", "sen kimsin", "kendini tanıt", "bot musun", "nesin sen"]):
            response = random.choice(self.categorized_answers["identity"])
        else:
            # Check for patterns in greetings
            for pattern, replies in self.greetings.items():
                if re.search(pattern, message.lower()):
                    response = random.choice(replies)
                    break
                
        await ctx.reply(response)
        
    @commands.Cog.listener()
    async def on_message(self, message):
        # Skip messages from bots including itself
        if message.author.bot:
            return
            
        # Only respond if the bot is mentioned
        if self.bot.user.mentioned_in(message):
            content = message.content.lower().replace(f'<@!{self.bot.user.id}>', '').replace(f'<@{self.bot.user.id}>', '').strip()
            
            # Check for identity questions
            if any(word in content for word in ["kimsin", "sen kimsin", "kendini tanıt", "bot musun", "nesin sen"]):
                await message.reply(random.choice(self.categorized_answers["identity"]))
                return
            
            # Check if it's a question
            if content.endswith("?"):
                # Check for time related questions
                if any(word in content for word in ["ne zaman", "zaman", "süre", "saat"]):
                    response = random.choice(self.categorized_answers["time"])
                # Check for decision related questions
                elif any(word in content for word in ["yapmalı mıyım", "etmeli miyim", "karar", "seçmeli miyim"]):
                    response = random.choice(self.categorized_answers["decision"])
                # Check for prediction related questions
                elif any(word in content for word in ["olacak mı", "gerçekleşecek mi", "başarılı olacak mıyım"]):
                    response = random.choice(self.categorized_answers["prediction"])
                # Use default responses for any other question
                else:
                    response = random.choice(self.responses)
                await message.reply(response)
                return
                
            # Check for greetings or other patterns
            for pattern, replies in self.greetings.items():
                if re.search(pattern, content):
                    await message.reply(random.choice(replies))
                    return
                    
            # Default response when bot is mentioned but no pattern matched
            await message.reply("Merhaba! Bir şey mi sormak istiyorsunuz? `/sorusor` komutunu kullanabilirsiniz.")

async def setup(bot):
    await bot.add_cog(Answer(bot))