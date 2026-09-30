import discord
from discord.ext import commands
from discord import app_commands

class Configuration(commands.GroupCog, name="config"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setup", description="Configure server security and ticket paths.")
    @app_commands.checks.has_permissions(administrator=True)
    async def config_setup(self, interaction: discord.Interaction, unverified_role: discord.Role, verified_role: discord.Role, log_channel: discord.TextChannel, ticket_category: discord.CategoryChannel = None):
        category_id = ticket_category.id if ticket_category else None
        
        async with self.bot.db.cursor() as cursor:
            await cursor.execute("""
                INSERT INTO server_config (guild_id, unverified_role_id, verified_role_id, ticket_category_id, log_channel_id)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET
                unverified_role_id=excluded.unverified_role_id,
                verified_role_id=excluded.verified_role_id,
                ticket_category_id=excluded.ticket_category_id,
                log_channel_id=excluded.log_channel_id
            """, (interaction.guild_id, unverified_role.id, verified_role.id, category_id, log_channel.id))
        await self.bot.db.commit()
        await interaction.response.send_message(f"✅ **Configuration Saved!** Log channel set to {log_channel.mention}.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Configuration(bot))
  
