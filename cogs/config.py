import discord
from discord.ext import commands

class Configuration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='config')
    @commands.has_permissions(administrator=True)
    async def config(self, ctx, unverified_id: int, verified_id: int, category_id: int = None):
        async with self.bot.db.cursor() as cursor:
            await cursor.execute("""
                INSERT INTO server_config (guild_id, unverified_role_id, verified_role_id, ticket_category_id)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET
                unverified_role_id=excluded.unverified_role_id,
                verified_role_id=excluded.verified_role_id,
                ticket_category_id=excluded.ticket_category_id
            """, (ctx.guild.id, unverified_id, verified_id, category_id))
        await self.bot.db.commit()
        await ctx.send("✅ **Server Configuration saved successfully!** You can now run `.setup` to spawn your panel frames here.")

    @config.error
    async def config_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❌ **Usage Format:** `.config [UnverifiedRoleID] [VerifiedRoleID] [Optional-TicketCategoryID]`")

async def setup(bot):
    await bot.add_cog(Configuration(bot))
  
