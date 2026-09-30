import discord
from discord.ext import commands
from discord import app_commands

class Announcements(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="announce", description="Broadcast a highly decorated, executive-styled announcement to a specific channel.")
    @app_commands.describe(
        target_channel="The destination text channel where the broadcast will be transmitted.",
        heading="The main prominent uppercase summary title header line.",
        message="The primary text body content copy for this network announcement."
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def announce_slash(
        self, 
        interaction: discord.Interaction, 
        target_channel: discord.TextChannel, 
        heading: str, 
        message: str
    ):
        # Acknowledge interaction immediately via an ephemeral response
        await interaction.response.defer(ephemeral=True)

        # Luxury Gold Art Deco styling matching the premium payment themes
        embed = discord.Embed(
            title=f"⚜️  {heading.upper()}  ⚜️",
            description=f"\n**{message}**\n", # Enforces bold treatment across message contents globally
            color=0xD4AF37 # Premium Metallic Gold Hex Accent
        )

        # Clean aesthetic layout dividers
        embed.add_field(
            name="🤖 NETWORK NOTICE", 
            value="***Please review the broadcast updates above carefully. If you require private technical assistance, open a ticket workspace session inside our service panel hub.***", 
            inline=False
        )

        # Global administrative authority signatures decoration
        embed.set_footer(
            text=f"Authorized Release • Dispatched by {interaction.user.name}",
            icon_url=interaction.user.display_avatar.url
        )
        embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)

        try:
            # Send the decorated template copy straight into the admin's selected channel path
            await target_channel.send(embed=embed)
            await interaction.followup.send(f"✅ **Announcement broadcast successfully deployed straight into** {target_channel.mention}!", ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send(f"❌ **Transmission Blocked.** I do not possess sufficient permission metrics to post text content inside {target_channel.mention}.", ephemeral=True)

    # Error translation handlers if non-admins try execution sequences
    @announce_slash.error
    async def announce_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("❌ **Privilege Error:** Administrative authority keys are required to transmit global network bulletins.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Announcements(bot))
  
