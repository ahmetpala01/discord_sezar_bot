import discord
from discord.ext import commands
from database import add_moderation_action, get_moderation_actions

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='warn')
    async def warn_user(self, ctx, member: discord.Member, *, reason: str):
        add_moderation_action(member.id, 'warn', reason)
        await ctx.send(f'{member.mention} uyarıldı. Sebep: {reason}')

    @commands.command(name='warnings')
    async def list_warnings(self, ctx, member: discord.Member):
        actions = get_moderation_actions(member.id)
        if actions:
            response = f'{member.mention} kullanıcısının uyarıları:\n'
            for action in actions:
                response += f'Tip: {action[0]}, Sebep: {action[1]}, Tarih: {action[2]}\n'
        else:
            response = f'{member.mention} kullanıcısının herhangi bir uyarısı bulunmamaktadır.'
        await ctx.send(response)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
