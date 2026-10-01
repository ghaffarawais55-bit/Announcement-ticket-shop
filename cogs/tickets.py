import discord
from discord.ext import commands
from discord import app_commands
import chat_exporter
import io
import asyncio

# 🔒 PROFESSIONAL ACTION BAR: Handles Claim & Close Operations
class TicketActionBarView(discord.ui.View):
    def __init__(self, bot, creator_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.creator_id = creator_id
        self.claimed_by = None

    @discord.ui.button(label="Claim Ticket", style=discord.ButtonStyle.primary, custom_id="claim_ticket_btn", emoji="🙋‍♂️")
    async def claim_click(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Fetch the staff role from the configuration database to verify permissions
        async with self.bot.db.execute("SELECT staff_role_id FROM ticket_config WHERE guild_id=?", (interaction.guild_id,)) as cursor:
            row = await cursor.fetchone()
        
        staff_role_id = row[0] if row else None
        
        # Check if user has the administrative staff role or admin permissions
        if staff_role_id and discord.utils.get(interaction.user.roles, id=staff_role_id) is None and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ **Access Denied:** Only verified staff elements can claim this session.", ephemeral=True)

        if self.claimed_by:
            return await interaction.response.send_message(f"⚠️ This ticket is already being handled by {self.claimed_by.mention}.", ephemeral=True)

        self.claimed_by = interaction.user
        button.disabled = True
        button.label = "Ticket Claimed"
        button.style = discord.ButtonStyle.secondary
        
        # Restructure channel permissions exclusively to the creator and the claiming staff member
        overwrites = interaction.channel.overwrites
        creator_obj = interaction.guild.get_member(self.creator_id)
        
        if creator_obj:
            overwrites[creator_obj] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        
        # Restrict generic staff visibility roles down to prevent chat room clutter
        if staff_role_id:
            staff_role = interaction.guild.get_role(staff_role_id)
            if staff_role:
                overwrites[staff_role] = discord.PermissionOverwrite(view_channel=True, send_messages=False)
                
        overwrites[interaction.user] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        await interaction.channel.edit(overwrites=overwrites)
        
        claim_embed = discord.Embed(
            description=f"🔹 **This support ticket has been claimed by {interaction.user.mention}.** They will handle your request from this point forward.",
            color=0x3b82f6
        )
        await interaction.response.edit_message(view=self)
        await interaction.channel.send(embed=claim_embed)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket_system_btn", emoji="🔒")
    async def close_click(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = interaction.channel
        guild = interaction.guild

        async with self.bot.db.execute("SELECT log_channel_id FROM ticket_config WHERE guild_id=?", (interaction.guild_id,)) as cursor:
            row = await cursor.fetchone()
        log_channel_id = row[0] if row else None

        await interaction.response.send_message("🔒 **Archiving session tracks and compiling HTML history transcripts...**")

        # Compile chat log data directly from the text channel channel
        transcript = await chat_exporter.export(channel)
        if transcript is None:
            return await channel.send("❌ Error capturing log data stream.")

        file_log = discord.File(io.BytesIO(transcript.encode()), filename=f"transcript-{channel.name}.html")
        file_dm = discord.File(io.BytesIO(transcript.encode()), filename=f"transcript-{channel.name}.html")

        creator_obj = guild.get_member(self.creator_id)

        # Send an elegant final receipt summary to the ticket user's DM box layout
        if creator_obj:
            try:
                dm_embed = discord.Embed(
                    title="📜 SERVICE TRANSACTION RECEIPT", 
                    description=f"Your support instance inside **{guild.name}** has been securely finalized.", 
                    color=0xD4AF37
                )
                dm_embed.add_field(name="🔹 Ticket ID Room", value=f"`{channel.name}`", inline=True)
                dm_embed.add_field(name="🔹 Handled By", value=self.claimed_by.mention if self.claimed_by else "`Unassigned Staff`", inline=True)
                await creator_obj.send(embed=dm_embed, file=file_dm)
            except discord.Forbidden: 
                pass

        # Broadcast the file audit transcript straight into the tracking log channel choice
        if log_channel_id:
            log_chan = guild.get_channel(log_channel_id)
            if log_chan:
                log_embed = discord.Embed(title="🔴 Ticket Session Terminated", color=0xef4444, timestamp=interaction.created_at)
                log_embed.add_field(name="Room Channel", value=f"`{channel.name}`", inline=True)
                log_embed.add_field(name="Opened By", value=f"<@{self.creator_id}>", inline=True)
                log_embed.add_field(name="Closed By", value=interaction.user.mention, inline=True)
                await log_chan.send(embed=log_embed, file=file_log)

        await asyncio.sleep(5)
        try: 
            await channel.delete()
        except Exception: 
            pass

# 🎫 DROPDOWN SELECTION MODULE WIDGET
class TicketPanelSelect(discord.ui.Select):
    def __init__(self, config):
        self.config = config
        options = [
            discord.SelectOption(label="General Support", description="Inquiries regarding server features.", emoji="❓", value="general"),
            discord.SelectOption(label="Payment & Premium", description="Process luxury transaction QR checkouts.", emoji="💰", value="payment"),
            discord.SelectOption(label="Report Player", description="Report rule breakers directly to staff.", emoji="🛡️", value="report")
        ]
        super().__init__(placeholder="Select your ticket topic category...", min_values=1, max_values=1, options=options, custom_id="ticket_dropdown")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(TicketCreationReasonModal(self.config, self.values[0]))

class TicketMenuView(discord.ui.View):
    def __init__(self, config):
        super().__init__(timeout=None)
        self.add_item(TicketPanelSelect(config))

# 📝 POPUP INPUT FORM MODAL WINDOW HANDLER
class TicketCreationReasonModal(discord.ui.Modal, title="Open Support Ticket"):
    reason = discord.ui.TextInput(
        label="Reason for opening this session:",
        style=discord.TextStyle.paragraph,
        placeholder="Provide all necessary details or paste payment screenshot handles...",
        required=True
    )

    def __init__(self, config, ticket_type):
        super().__init__()
        self.config = config
        self.ticket_type = ticket_type

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        
        # Row Tuple Map Positions: (0: guild_id, 1: ticket_category_id, 2: staff_role_id, 3: log_channel_id)
        category_id = self.config[1] if self.config else None
        staff_role_id = self.config[2] if self.config else None
        log_channel_id = self.config[3] if self.config else None

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        }
        
        if staff_role_id:
            staff_role = guild.get_role(staff_role_id)
            if staff_role:
                overwrites[staff_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

        category = guild.get_channel(category_id) if category_id else None
        channel_name = f"{self.ticket_type}-{interaction.user.name}"
        
        ticket_channel = await guild.create_text_channel(name=channel_name, category=category, overwrites=overwrites)

        embed = discord.Embed(
            title=f"🎫 Ticket Session: {self.ticket_type.upper()}",
            description=f"Welcome {interaction.user.mention}! Support handlers have been notified.\n\n**Stated Objective:**\n```\n{self.reason.value}\n```",
            color=0x3b82f6
        )
        embed.set_footer(text="Staff members can claim this session below. Click lock to close.")
        
        # Attach dynamic action bar view tracked right to the user's account Snowflake ID
        view = TicketActionBarView(interaction.client, interaction.user.id)
        
        await ticket_channel.send(content=f"{interaction.user.mention} | Help Desk Group", embed=embed, view=view)
        await interaction.followup.send(f"✅ Ticket opened successfully: {ticket_channel.mention}", ephemeral=True)

        if log_channel_id:
            log_chan = guild.get_channel(log_channel_id)
            if log_chan:
                log_embed = discord.Embed(title="🟢 Ticket Created", color=0x10b981, timestamp=interaction.created_at)
                log_embed.add_field(name="User", value=interaction.user.mention, inline=True)
                log_embed.add_field(name="Topic", value=self.ticket_type.upper(), inline=True)
                log_embed.add_field(name="Channel", value=ticket_channel.mention, inline=True)
                await log_chan.send(embed=log_embed)

# ⚙️ COG CONTROL STRUCTURE CLASS
