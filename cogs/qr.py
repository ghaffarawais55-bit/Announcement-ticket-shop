import discord
from discord.ext import commands

class QRCode(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Enforce case-insensitive matching handle for both .qr and .QR formats
    @commands.command(name='qr', aliases=['QR'])
    async def qr_payment(self, ctx, amount: str = None):
        # Premium Luxury Art Deco Design Theme (Hex Match: #D4AF37 Metallic Gold)
        embed = discord.Embed(
            title="🔹 DBS MART PREMIUM CHECKOUT 🔹",
            description=(
                "Your advanced ticketing transaction request requires verified deposit confirmation.\n"
                "Please scan the terminal matrix below using your banking application to proceed."
            ),
            color=0xD4AF37
        )

        # Dynamic pricing evaluator processing module
        if amount:
            # Strip away any accidental currency symbols typed by users (\$ or ₹) to keep numbers clean
            clean_amount = amount.replace(r"\$", "").replace("₹", "").replace("rs", "").strip()
            
            # Formats the amount cleanly into a bold, executive billing line item box
            embed.add_field(
                name="🔸 REQUESTED INVOICE BALANCE",
                value=f"```\nTOTAL DUE: INR {clean_amount}.00\n```",
                inline=False
            )
        else:
            # Fallback block if the user just types a standard '.qr' without an amount parameter
            embed.add_field(
                name="🔸 REQUESTED INVOICE BALANCE",
                value="```\nTOTAL DUE: PENDING VERIFICATION\n```",
                inline=False
            )

        # 🚀 UPDATED LINK: Points directly to your secure raw Discord image payload path
        embed.set_image(url="https://cdn.discordapp.com/attachments/1554557543777312869/1555107650222563379/DBS_MART_perfect_QR_poster.png?backend=b2&ex=6abf525c&is=6abe00dc&hm=40d3dd6f92c83772089d7fb792ce54fc35c0f0f828b46884c27a7dfeb47979a1")

        # High-end typographic data grid layout
        embed.add_field(
            name="🔸 SETTLE HANDLE",
            value="`7459013159@superyes`",
            inline=True
        )
        embed.add_field(
            name="🔸 ROUTING CORE",
            value="**YES BANK** • *Baroda Gateway*",
            inline=True
        )

        # Clean, non-emoji technical structural footer configuration
        embed.set_footer(
            text="Secured Interoperable Network | File your payment receipt screenshot inside a private ticket immediately.",
            icon_url=ctx.guild.icon.url if ctx.guild.icon else None
        )

        # Clear original user messaging triggers automatically to keep the channel logs tidy
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(QRCode(bot))
  
