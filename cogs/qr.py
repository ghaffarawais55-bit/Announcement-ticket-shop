import discord
from discord.ext import commands
from discord import app_commands

class QRCode(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="qr", description="Display the premium luxury payment processing terminal interface.")
    async def qr_slash(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="✨ LUXURY TICKETING CHECKOUT ✨",
            description=(
                "Your advanced request requires verified deposit confirmation.\n"
                "Please scan the premium checkout matrix below using your banking app to authorize processing."
            ),
            color=0xD4AF37
        )
        embed.set_image(url="https://githubusercontent.com")
        
        embed.add_field(name="⚜️ Registered Merchant Account", value="`7459013159@superyes`", inline=False)
        embed.add_field(name="🏛️ Bank Settlement Gateway", value="**YES BANK** • *Bank of Baroda Router*", inline=True)
        embed.add_field(name="🔒 Security Cleared", value="`Encrypted Interoperable UPI`", inline=True)
        
        embed.set_footer(
            text="Powered by Executive Pay • File your transfer receipt screenshot inside a private ticket session immediately.",
            icon_url=interaction.guild.icon.url if interaction.guild.icon else None
        )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(QRCode(bot))
  
