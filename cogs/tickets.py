import discord
from discord.ext import commands
from discord import app_commands
import chat_exporter
import io
import asyncio

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

class TicketCreationReasonModal(discord.ui.Modal, title="Open Support Ticket"):
    reason = discord.ui.TextInput(
        label="Reason for opening this session:",
        style=discord.TextStyle.paragraph,
        placeholder="Provide all necessary details or paste payment screenshots handles...",
        required=True
    )

    def __init__(self, config, ticket_type):
        super().__init__()
        self.config = config # db row configuration values map
        self.ticket_type = ticket_type

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        
        category_id = self.config[1]
        staff_role_id = self.config[2]
        log_channel_id = self.config[3]

        # Base Permissions setup
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
        
        view = discord.ui.View(timeout=None)
        view.add_item(discord.ui.Button(label="Close Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket_system_btn", emoji="🔒"))
        
        await ticket_channel.send(content=f"{interaction.user.mention} | Help Desk", embed=embed, view=view)
        await interaction.followup.send(f"✅ Ticket opened successfully: {ticket_channel.mention}", ephemeral=True)

        # Log Ticket Creation Activity Monitor
        if log_channel_id:
            log_chan = guild.get_channel(log_channel_id)
            if log_chan:
                log_embed = discord.Embed(title="🟢 Ticket Created", color=0x10b981, timestamp=interaction.created_at)
                log_embed.add_field(name="User", value=interaction.user.mention, inline=True)
                log_embed.add_field(name="Topic", value=self.ticket_type.upper(), inline=True)
                log_embed.add_field(name="Channel", value=ticket_channel.mention, inline=True)
                await log_chan.send(embed=log_embed)

class ProfessionalTickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if not interaction.data or interaction.data.get("custom_id") != "close_ticket_system_btn":
            return

        channel = interaction.channel
        guild = interaction.guild

        async with self.bot.db.execute("SELECT * FROM ticket_config WHERE guild_id=?", (interaction.guild_id,)) as cursor:
            config = await cursor.fetchone()

        await interaction.response.send_message("🔒 **Archiving session and creating interactive HTML transcripts...**")

        transcript = await chat_exporter.export(channel)
        if transcript is None:
            return await channel.send("❌ Error capturing log data stream.")

        transcript_file_log = discord.File(io.BytesIO(transcript.encode()), filename=f"transcript-{channel.name}.html")
        transcript_file_dm = discord.File(io.BytesIO(transcript.encode()), filename=f"transcript-{channel.name}.html")

        creator_name = channel.name.split('-')[-1]
        ticket_creator = discord.utils.get(guild.members, name=creator_name)

        if ticket_creator:
            try:
                dm_embed = discord.Embed(title="📜 Ticket Closure Summary", description=f"Your ticket inside **{guild.name}** has been closed. An interactive copy of your chat history is attached.", color=0x3b82f6)
                await ticket_creator.send(embed=dm_embed, file=transcript_file_dm)
            except discord.Forbidden: pass

        if config and config[3]:
            log_chan = guild.get_channel(config[3])
            if log_chan:
                log_embed = discord.Embed(title="🔴 Ticket Closed & Archived", color=0xef4444, timestamp=interaction.created_at)
                log_embed.add_field(name="Channel Closed", value=channel.name, inline=True)
                log_embed.add_field(name="Closed By", value=interaction.user.mention, inline=True)
                await log_chan.send(embed=log_embed, file=transcript_file_log)

        await asyncio.sleep(5)
        try: await channel.delete()
        except Exception: pass

    @app_commands.command(name="setup-tickets", description="Configure ticket processing category limits and launch ticket creation selection panels.")
    @app_commands.describe(
        target_channel="The channel where the ticket creation selection panels embed will be displayed.",
        ticket_category="The targeted custom category folder under which new ticket channels open up.",
        staff_role="The administrative role granted helper view access to private tickets.",
        log_channel="The destination text channel where chat text transcripts are archived."
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_tickets(self, interaction: discord.Interaction, target_channel: discord.TextChannel, ticket_category: discord.CategoryChannel, staff_role: discord.Role, log_channel: discord.TextChannel):
        await interaction.response.defer(ephemeral=True)

        async with self.bot.db.cursor() as cursor:
            await cursor.execute("""
                INSERT INTO ticket_config (guild_id, ticket_category_id, staff_role_id, log_channel_id)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET
                ticket_category_id=excluded.ticket_category_id, staff_role_id=excluded.staff_role_id, log_channel_id=excluded.log_channel_id
            """, (interaction.guild_id, ticket_category.id, staff_role.id, log_channel.id))
        await self.bot.db.commit()

        async with self.bot.db.execute("SELECT * FROM ticket_config WHERE guild_id=?", (interaction.guild_id,)) as cursor:
            config = await cursor.fetchone()

        embed = discord.Embed(
            title="🎫 Premium Help Desk Hub",
            description=(
                "Need assistance or filing an advance payment transaction screen registration?\n\n"
                "Select your target support topic path from the dropdown component down below to open a direct private room session."
            ),
            color=0x3b82f6
        )
        embed.set_footer(text="Official Server Support Infrastructure Router Enabled")

        await target_channel.send(embed=embed, view=TicketMenuView(config))
        await interaction.followup.send(f"✅ Professional ticket creation desk interface spawned inside {target_channel.mention}!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ProfessionalTickets(bot))
                                                                     
