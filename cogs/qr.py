import discord
from discord.ext import commands

class QRCode(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='qr')
    async def qr(self, ctx):
        # Premium Luxury Art Deco Theme (Hex Match: #D4AF37 Gold)
        embed = discord.Embed(
            title="✨ LUXURY TICKETING CHECKOUT ✨",
            description=(
                "Your advanced request requires verified deposit confirmation.\n"
                "Please scan the premium checkout matrix below using your banking app to authorize processing."
            ),
            color=0xD4AF37
        )
        
        # Points directly to your newly decorated luxury QR image asset hosted in your repository
        embed.set_image(url="https://githubusercontent.com")
        
        # Clean multi-server billing breakdown
        embed.add_field(
            name="⚜️ Registered Merchant Account", 
            value="`7459013159@superyes`", 
            inline=False
        )
        embed.add_field(
            name="🏛️ Bank Settlement Gateway", 
            value="**YES BANK** • *Bank of Baroda Router*", 
            inline=True
        )
        embed.add_field(
            name="🔒 Security Cleared", 
            value="`Encrypted Interoperable UPI`", 
            inline=True
        )
        
        # Dynamic footer that adapts beautifully to any public server it is added to
        embed.set_footer(
            text="Powered by Executive Pay • File your transfer receipt screenshot inside a private ticket session immediately.",
            icon_url=ctx.guild.icon.url if ctx.guild.icon else None
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(QRCode(bot))
  
