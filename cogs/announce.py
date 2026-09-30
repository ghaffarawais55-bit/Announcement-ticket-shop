import discord
from discord.ext import commands

class Announcements(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='announce')
    @commands.has_permissions(administrator=True)
    async def announce(self, ctx, *, text: str):
        embed = discord.Embed(
            title="📢 Server Network Announcement",
            description=text,
            color=0xf59e0b
        )
        embed.set_footer(text=f"Dispatched by Admin: {ctx.author.name}")
        await ctx.send(embed=embed)
        await ctx.message.delete()

async def setup(bot):
    await bot.add_cog(Announcements(bot))
  
