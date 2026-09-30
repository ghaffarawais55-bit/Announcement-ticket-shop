import discord
from discord.ext import commands
from discord import app_commands
import chat_exporter
import io
import asyncio

# 1. MULTI-PANEL TYPE SELECTION DROPDOWN
class TicketPanelSelect(discord.ui.Select):
    def __init__(self, config):
        self.config = config # DB Config row values mapped
        options = [
            discord.SelectOption(label="General Support", description="Get assistance with general server inquiries.", emoji="❓", value="general"),
            discord.SelectOption(label="Payment & Billing", description="Open a ticket to process premium QR codes.", emoji="💰", value="payment"),
            discord.SelectOption(label="Report a Player", description="Report rule breakers or server issues.", emoji="🛡️", value="report")
        ]
        super().__init__(placeholder="Select the type of ticket you need...", min_values=1, max_values=1, options=options, custom_id="panel_select")

    async def callback(self, interaction: discord.Interaction):
        ticket_type = self.values[0]
        await interaction.response.send_modal(AdvancedTicketModal(self.config, ticket_type))

class MultiPanelView(discord.ui.View):
    def __init__(self, config):
        super().__init__(timeout=None)
        self.add_item(TicketPanelSelect(config))

# 2. POPUP INPUT FORM MODAL WINDOW
class AdvancedTicketModal(discord.ui.Modal, title="Open Support Ticket"):
    reason = discord.ui.TextInput(
        label="Describe your query / deposit proof:",
        style=discord.TextStyle.paragraph,
        placeholder="Provide as much detailed description as possible...",
        required=True
    )

    def __init__(self, config, ticket_type):
        super().__init__()
        self.config = config
        self.ticket_type = ticket_type

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        category_id = self.config[3]
        log_channel_id = self.config[4]
        staff_role_id = self.config[2]

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        }
        
        if staff_role_id:
            staff_role = guild.get_role(staff_role_id)
            if staff_role:
                overwrites[staff_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        category = guild.get_channel(category_id) if category_id else None
        
        # Build clean channel tags matching panel choices
        channel_name = f"{self.ticket_type}-{interaction.user.name}"
        ticket_channel = await guild.create_text_channel(name=channel_name, category=category, overwrites=overwrites)

        embed = discord.Embed(
            title=f"🎫 Ticket Opened: {self.ticket_type.upper()}",
            description=f"Welcome {interaction.user.mention}! Support staff will assist you shortly.\n\n**Stated Objective:**\n```\n{self.reason.value}\n```",
            color=0x3b82f6
        )
        
        view = discord.ui.View(timeout=None)
        view.add_item(discord.ui.Button(label="Close Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket", emoji="🔒"))
        
        await ticket_channel.send(content=f"{interaction.user.mention} | Staff Notification", embed=embed, view=view)
        await interaction.followup.send(f"✅ Ticket channel provisioned successfully: {ticket_channel.mention}", ephemeral=True)

        # 📢 AUTO-MONITORING LOG: Broadcast ticket creation event
        if log_channel_id:
            log_chan = guild.get_channel(log_channel_id)
            if log_chan:
                log_embed = discord.Embed(title="🟢 Ticket Created", color=0x10b981, timestamp=interaction.created_at)
                log_embed.add_field(name="User", value=interaction.user.mention, inline=True)
                log_embed.add_field(name="Type", value=self.ticket_type.upper(), inline=True)
                log_embed.add_field(name="Channel", value=ticket_channel.mention, inline=True)
                await log_chan.send(embed=log_embed)

# 3. VERIFICATION PERSISTENT MODULE PANELS
class VerificationControlView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Verify Account", style=discord.ButtonStyle.success, custom_id="verify_user", emoji="✅")
    async def verify_click(self, interaction: discord.Interaction, button: discord.ui.Button):
        async with self.bot.db.execute("SELECT * FROM server_config WHERE guild_id=?", (interaction.guild_id,)) as cursor:
            config = await cursor.fetchone()
        
        if not config:
            return await interaction.response.send_message("❌ This server is unconfigured.", ephemeral=True)

        unverified_role = interaction.guild.get_role(config[1])
        verified_role = interaction.guild.get_role(config[2])

        try:
            if verified_role: await interaction.user.add_roles(verified_role)
            if unverified_role: await interaction.user.remove_roles(unverified_role)
            await interaction.response.send_message("✅ Identity verified! Welcome.", ephemeral=True)
        except Exception:
            await interaction.response.send_message("❌ Role assignment error. Check bot ranking hierarchy.", ephemeral=True)

# MAIN TICKETING IMPLEMENTATION COG
class AdvancedTicketsEngine(commands.Cog):
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
        if not interaction.data or interaction.data.get("custom_id") != "close_ticket":
            return

        channel = interaction.channel
        guild = interaction.guild

        async with self.bot.db.execute("SELECT * FROM server_config WHERE guild_id=?", (interaction.guild_id,)) as cursor:
            config = await cursor.fetchone()

        await interaction.response.send_message("🔒 **Archiving chat and extracting automated HTML transcripts...**")

        # 📄 AUTOMATED TRANSCRIPT GENERATION
        transcript = await chat_exporter.export(channel)
        if transcript is None:
            return await channel.send("❌ Error extracting transcript trace records.")

        transcript_file_log = discord.File(io.BytesIO(transcript.encode()), filename=f"transcript-{channel.name}.html")
        transcript_file_dm = discord.File(io.BytesIO(transcript.encode()), filename=f"transcript-{channel.name}.html")

        # Target components for user dm generation routing safely
        creator_name = channel.name.replace("general-", "").replace("payment-", "").replace("report-", "")
        ticket_creator = discord.utils.get(guild.members, name=creator_name)

        # 📬 TRANSCRIPT AUTO-LOG TO USER DM
        if ticket_creator:
            try:
                dm_embed = discord.Embed(title="📜 Ticket Closure Summary", description=f"Your ticket transaction environment inside **{guild.name}** has been closed. An interactive copy of your chat history is attached below.", color=0x3b82f6)
                await ticket_creator.send(embed=dm_embed, file=transcript_file_dm)
            except discord.Forbidden:
                print(f"Could not DM transcript to {creator_name} (DMs are turned off).")

        # 📢 TRANSCRIPT AUTO-LOG TO SERVER LOG CHANNEL
        if config and config[4]:
            log_chan = guild.get_channel(config[4])
            if log_chan:
                log_embed = discord.Embed(title="🔴 Ticket Closed & Archived", color=0xef4444, timestamp=interaction.created_at)
                log_embed.add_field(name="Channel Closed", value=channel.name, inline=True)
                log_embed.add_field(name="Closed By", value=interaction.user.mention, inline=True)
                await log_chan.send(embed=log_embed, file=transcript_file_log)

        await asyncio.sleep(3)
        await channel.delete()

    @app_commands.command(name="panels", description="Spawn verification and multi-panel ticketing system embeds.")
    @app_commands.checks.has_permissions(administrator=True)
    async def spawn_panels(self, interaction: discord.Interaction):
        async with self.bot.db.execute("SELECT * FROM server_config WHERE guild_id=?", (interaction.guild_id,)) as cursor:
            config = await cursor.fetchone()
        if not config:
            return await interaction.response.send_message("❌ Server metrics unconfigured. Run `/config setup` first.", ephemeral=True)

        v_embed = discord.Embed(title="🛡️ Security Identity Gateway", description="Click below to complete security verification validation overlays and explore the network channels.", color=0x10b981)
        t_embed = discord.Embed(title="🎫 Premium Assistance Hub", description="Open a private support session. Select your matching problem space from the option dropdown component below.", color=0x3b82f6)
        
        await interaction.response.send_message("🚀 Displaying administrative layout modules panels...", ephemeral=True)
        await interaction.channel.send(embed=v_embed, view=VerificationControlView(self.bot))
        await interaction.channel.send(embed=t_embed, view=MultiPanelView(config))

async def setup(bot):
    await bot.add_cog(AdvancedTicketsEngine(bot))
  
