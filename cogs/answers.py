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
            "Hayır katılmıyorum!",
            "Belki de öyledir",
            "Bilmiyorum, ama denemeye değer",
            "Bunu düşünmek zorundayım",
            "Bunu yapmayı çok isterim",
            "Bunu yapmayı hiç istemiyorum",
            "Hayır öyle düşünmüyorum",
            "Evet kesinlikle yapmalısın!",
        ]
        
        # Greetings and casual chat responses
        self.greetings = {
            r"merhaba|selam|hey|hi|hello|sa|sea|selamın aleyküm": [
                "Aleyküm selam gardaş",
                "Selam dostum! Nasılsın?",
                "Hg reis as",
                "Kölelikte bugun nasıl gidiyor?",
                "Merhaba! Nasıl yardımcı olabilirim?",
                "Selam! Bugün sana nasıl yardım edebilirim?",
                "Hey! Ne yapıyorsun?",
            ],
            r"nasılsın|naber|ne haber": [
                "İyi aga seni sormalı?",
                "İyiyim, teşekkürler! Sen nasılsın?",
                "Harika! Sen nasılsın?",
                "Bir bot olarak her zamanki gibiyim. Sen nasılsın?",
                "Botlar yorulmazlar her zaman iyiyiz gardeş ;)",
            ],
            r"teşekkür|teşekkürler|sağol|eyw|eyw reis|eyv|eyv reis": [
                "Ne demek bro!",
                "Rica ederim!",
                "Ne demek, her zaman!",
                "Yardımcı olabildiysem ne mutlu bana!",
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
                "Bu senin kararın olmalı, ama bence denemelisin.",
                "Bunu yapmak istediğine gerçekten emin misin?",
                "Eğer gerçekten istiyorsan yapmalısın!",
                "Bazen beklemek en iyisidir.",
            ],
            "prediction": [
                "Geleceği görebilseydim sana söylerdim!",
                "Büyük ihtimalle evet!",
                "Sanırım bu olmayacak.",
                "Gökyüzündeki yıldızlar buna olumlu bakıyor!",
            ],
            "djkavun":[
                "Kavun mu, offf sulu suluuu",
                "Kavun yarmayı çok severim",
                "Ortadan ayırmak için buradayım",
                "Kavun yarmak için buradayım",
                "Dur bıçağı alayım da kavunu yarayım",
                "Kavun yarma işini ben üstlenirim",
                "Sen olmazsan kavunu kim yaracak?",
                "Kavunu bir tek sen yarabilirsin",
                "Kavun mu yarıyoruz, offf sulu sulu en sevdiğim"
            ],
            "salemanageribo":[
                "Satış elemanı ibo burada mıymış ?",
                "İbo gelmiş, satış elemanı ibo burada",
                "Vaayy furkan yok galiba ibo bey gelmiş",
                "Dilci furkan yoksa satış elemanı buradadır",
                "İbo bey gelmiş, furkan yok mu?",
            ]
        }

    @commands.hybrid_command(name="sorusor", description="Bir cevap istiyorsan alırsın")
    async def ask_question(self, ctx, *, question: str):
        # Categorize the question if possible
        if any(word in question.lower() for word in ["ne zaman", "zaman", "süre", "saat"]):
            response = random.choice(self.categorized_answers["time"])
        elif any(word in question.lower() for word in ["yapmalı mıyım", "etmeli miyim", "karar", "seçmeli miyim"]):
            response = random.choice(self.categorized_answers["decision"])
        elif any(word in question.lower() for word in ["olacak mı", "gerçekleşecek mi", "başarılı olacak mıyım"]):
            response = random.choice(self.categorized_answers["prediction"])
        elif any(word in question.lower() for word in ["kavun", "kavun yar", "kavun yarma","kavunu kim yarar","sulu sulu kavun"]):
            response = random.choice(self.categorized_answers["djkavun"])
        elif any(word in question.lower() for word in ["ibo", "ibo bey", "ibo gelmiş", "ibo nerede","ibo nerede lan"]):
            response = random.choice(self.categorized_answers["salemanageribo"])
        else:
            response = random.choice(self.responses)
            
        # Create a nice embed for the answer
        embed = discord.Embed(
            description=f"{response}",
            color=discord.Color.purple()
        )        
        await ctx.reply(embed=embed)
        
    @commands.hybrid_command(name="sohbet", description="Benimle sohbet et")
    async def chat(self, ctx, *, message: str):
        response = "Anlamadım, daha açık konuşabilir misin?"
        
        # Check for patterns in greetings
        for pattern, replies in self.greetings.items():
            if re.search(pattern, message.lower()):
                response = random.choice(replies)
                break
                
         # Check for kavun related messages
        if any(word in message.lower() for word in ["kavun", "kavun yar", "kavun yarma", "kavunu kim yarar", "sulu sulu kavun"]):
            response = random.choice(self.categorized_answers["djkavun"])
        
        # Check for ibo related messages
        elif any(word in message.lower() for word in ["ibo", "ibo bey", "ibo gelmiş", "ibo nerede", "ibo nerede lan"]):
            response = random.choice(self.categorized_answers["salemanageribo"])
                
        await ctx.reply(response)
        
    @commands.Cog.listener()
    async def on_message(self, message):
        # Skip messages from bots including itself
        if message.author.bot:
            return
            
        # Only respond if the bot is mentioned
        if self.bot.user.mentioned_in(message):
            content = message.content.lower().replace(f'<@!{self.bot.user.id}>', '').replace(f'<@{self.bot.user.id}>', '').strip()
            
            # Check if it's a question
            if content.endswith("?"):
                # Check for kavun related questions
                if any(word in content for word in ["kavun", "kavun yar", "kavun yarma", "kavunu kim yarar", "sulu sulu kavun"]):
                    response = random.choice(self.categorized_answers["djkavun"])
                # Check for ibo related questions
                elif any(word in content for word in ["ibo", "ibo bey", "ibo gelmiş", "ibo nerede", "ibo nerede lan"]):
                    response = random.choice(self.categorized_answers["salemanageribo"])
                # Check for time related questions
                elif any(word in content for word in ["ne zaman", "zaman", "süre", "saat"]):
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
            
            # Check for kavun related messages (without question mark)
            if any(word in content for word in ["kavun", "kavun yar", "kavun yarma", "kavunu kim yarar", "sulu sulu kavun"]):
                await message.reply(random.choice(self.categorized_answers["djkavun"]))
                return
                
            # Check for ibo related messages (without question mark)
            if any(word in content for word in ["ibo", "ibo bey", "ibo gelmiş", "ibo nerede", "ibo nerede lan"]):
                await message.reply(random.choice(self.categorized_answers["salemanageribo"]))
                return
                
            # Check for greetings or other patterns
            for pattern, replies in self.greetings.items():
                if re.search(pattern, content):
                    await message.reply(random.choice(replies))
                    return
                    
            # Default response when bot is mentioned but no pattern matched
            await message.reply("Merhaba! Bir şey mi sormak istiyorsun? `/sorusor` komutunu kullanabilirsin.")
async def setup(bot):
    await bot.add_cog(Answer(bot))