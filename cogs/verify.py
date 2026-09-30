import discord
from discord.ext import commands
from discord import app_commands

class VerifyButtonView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Verify Identity", style=discord.ButtonStyle.success, custom_id="gate_verify_btn", emoji="✅")
    async def verify_click(self, interaction: discord.Interaction, button: discord.ui.Button):
        async with self.bot.db.execute("SELECT * FROM verify_config WHERE guild_id=?", (interaction.guild_id,)) as cursor:
            config = await cursor.fetchone()
        
        if not config:
            return await interaction.response.send_message("❌ This server verification layout is not configured yet.", ephemeral=True)

        unverified_role = interaction.guild.get_role(config[1])
        verified_role = interaction.guild.get_role(config[2])

        try:
            if verified_role: 
                await interaction.user.add_roles(verified_role)
            if unverified_role: 
                await interaction.user.remove_roles(unverified_role)
            await interaction.response.send_message("🎉 **Verification Successful!** Welcome to the server.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ **Permissions Error:** Ensure the bot's role is higher than the roles it is assigning.", ephemeral=True)

class VerificationSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        async with self.bot.db.execute("SELECT unverified_role_id FROM verify_config WHERE guild_id=?", (member.guild.id,)) as cursor:
            row = await cursor.fetchone()
        if row and row[0]:
            role = member.guild.get_role(row[0])
            if role:
                try: await member.add_roles(role)
                except Exception: pass

    @app_commands.command(name="setup-verify", description="Configure server security auto-isolation and spawn verification panel.")
    @app_commands.describe(
        target_channel="The channel where the verification button panel will be sent.",
        unverified_role="The restricted role given automatically to joining accounts.",
        verified_role="The member role given when they successfully verify."
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_verify(self, interaction: discord.Interaction, target_channel: discord.TextChannel, unverified_role: discord.Role, verified_role: discord.Role):
        await interaction.response.defer(ephemeral=True)

        async with self.bot.db.cursor() as cursor:
            await cursor.execute("""
                INSERT INTO verify_config (guild_id, unverified_role_id, verified_role_id)
                VALUES (?, ?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET unverified_role_id=excluded.unverified_role_id, verified_role_id=excluded.verified_role_id
            """, (interaction.guild_id, unverified_role.id, verified_role.id))
        await self.bot.db.commit()

        embed = discord.Embed(
            title="🛡️ Server Verification Gateway",
            description=(
                "**Welcome to the server!**\n\n"
                "To protect our community against automated bot attacks, you must verify your identity.\n"
                "Click the button below to claim full server access channels."
            ),
            color=0x10b981
        )
        embed.set_footer(text="Identity Gate Protection System Securely Armed")

        await target_channel.send(embed=embed, view=VerifyButtonView(self.bot))
        await interaction.followup.send(f"✅ Security verification panel initialized inside {target_channel.mention}!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(VerificationSystem(bot))
              
