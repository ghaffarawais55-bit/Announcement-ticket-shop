import discord
from discord.ext import commands

class QRCode(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='qr', aliases=['QR'])
    async def qr_payment(self, ctx, amount: str = None):
        embed = discord.Embed(
            title="🔹 DBS MART PREMIUM CHECKOUT 🔹",
            description=(
                "Your advanced ticketing transaction request requires verified deposit confirmation.\n"
                "Please scan the terminal matrix below using your banking application to proceed."
            ),
            color=0xD4AF37
        )

        if amount:
            clean_amount = amount.replace(r"\$", "").replace("₹", "").replace("rs", "").strip()
            embed.add_field(
                name="🔸 REQUESTED INVOICE BALANCE",
                value=f"```\nTOTAL DUE: INR {clean_amount}.00\n```",
                inline=False
            )
        else:
            embed.add_field(
                name="🔸 REQUESTED INVOICE BALANCE",
                value="```\nTOTAL DUE: PENDING VERIFICATION\n```",
                inline=False
            )

        # 🚀 REPLACE THIS URL STRING WITH YOUR DIRECT COPIED DISCORD IMAGE LINK ROADMAP
        embed.set_image(url="https://githubusercontent.com")

        embed.add_field(name="🔸 SETTLE HANDLE", value="`7459013159@superyes`", inline=True)
        embed.add_field(name="🔸 ROUTING CORE", value="**YES BANK** • *Baroda Gateway*", inline=True)

        embed.set_footer(
            text="Secured Interoperable Network | File your payment receipt screenshot inside a private ticket immediately.",
            icon_url=ctx.guild.icon.url if ctx.guild.icon else None
        )

        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(QRCode(bot))
  
