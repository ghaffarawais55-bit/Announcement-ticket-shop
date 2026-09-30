import discord
from discord.ext import commands
import asyncio

class TicketReasonModal(discord.ui.Modal, title="Create Support Ticket"):
    reason = discord.ui.TextInput(
        label="Reason for opening this ticket?",
        style=discord.TextStyle.paragraph,
        placeholder="Describe your issue or paste payment transaction reference handles...",
        required=True
    )

    def __init__(self, config):
        super().__init__()
        self.config = config

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        category_id = self.config[3]
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        }
        
        if self.config[2]:
            staff_role = guild.get_role(self.config[2])
            if staff_role:
                overwrites[staff_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        category = guild.get_channel(category_id) if category_id else None
        
        ticket_channel = await guild.create_text_channel(
            name=f"ticket-{interaction.user.name}",
            category=category,
            overwrites=overwrites
        )

        embed = discord.Embed(
            title="🎫 Ticket Opened",
            description=f"Welcome {interaction.user.mention}! Support staff will be with you shortly.\n\n**Stated Reason:**\n```\n{self.reason.value}\n```",
            color=0x3b82f6
        )
        
        view = discord.ui.View(timeout=None)
        view.add_item(discord.ui.Button(label="Close Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket", emoji="🔒"))
        
        await ticket_channel.send(content=f"{interaction.user.mention} | Support Staff", embed=embed, view=view)
        await interaction.followup.send(f"✅ Ticket environment generated: {ticket_channel.mention}", ephemeral=True)

class InteractiveControlPanel(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Verify Identity", style=discord.ButtonStyle.success, custom_id="verify_user", emoji="✅")
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        async with self.bot.db.execute("SELECT * FROM server_config WHERE guild_id=?", (interaction.guild_id,)) as cursor:
            config = await cursor.fetchone()
        
        if not config:
            return await interaction.response.send_message("❌ This server parameters are unconfigured.", ephemeral=True)

        unverified_role = interaction.guild.get_role(config[1])
        verified_role = interaction.guild.get_role(config[2])

        try:
            if verified_role: await interaction.user.add_roles(verified_role)
            if unverified_role: await interaction.user.remove_roles(unverified_role)
            await interaction.response.send_message("✅ Identity verification checked successfully! Welcome to the server.", ephemeral=True)
        except Exception:
            await interaction.response.send_message("❌ Role processing failed. Verify bot role spacing hierarchy levels.", ephemeral=True)

    @discord.ui.button(label="Open Support Ticket", style=discord.ButtonStyle.primary, custom_id="open_ticket", emoji="📩")
    async def ticket_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        async with self.bot.db.execute("SELECT * FROM server_config WHERE guild_id=?", (interaction.guild_id,)) as cursor:
            config = await cursor.fetchone()
        if not config:
            return await interaction.response.send_message("❌ This server configurations are unlinked.", ephemeral=True)
        
        await interaction.response.send_modal(TicketReasonModal(config))

class TicketsEngine(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        async with self.bot.db.execute("SELECT unverified_role_id FROM server_config WHERE guild_id=?", (member.guild.id,)) as cursor:
            row = await cursor.fetchone()
        if row and row[0]:
            role = member.guild.get_role(row[0])
            if role:
                try: await member.add_roles(role)
                except Exception: pass

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.data and interaction.data.get("custom_id") == "close_ticket":
            await interaction.response.send_message("🔒 *Closing transaction ticket and wiping channel space in 5 seconds...*")
            await asyncio.sleep(5)
            try: await interaction.channel.delete()
            except Exception: pass

    @commands.command(name='setup')
    @commands.has_permissions(administrator=True)
    async def setup(self, ctx):
        async with self.bot.db.execute("SELECT * FROM server_config WHERE guild_id=?", (ctx.guild.id,)) as cursor:
            config = await cursor.fetchone()
        if not config:
            return await ctx.send("❌ This server is unconfigured. Link data options using `.config` first.")

        v_embed = discord.Embed(title="🛡️ Security Identity Gateway", description="Click the container link element button below to safely authorize entry privileges and discover full channels.", color=0x10b981)
        t_embed = discord.Embed(title="🎫 Assistance Support Hub", description="Initialize isolated channels to map order tracking options or process verified QR deposit entries.", color=0x3b82f6)
        
        view = InteractiveControlPanel(self.bot)
        await ctx.send(embed=v_embed)
        await ctx.send(embed=t_embed, view=view)
        await ctx.message.delete()

async def setup(bot):
    await bot.add_cog(TicketsEngine(bot))
      
