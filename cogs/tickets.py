import discord, io, asyncio, chat_exporter
from discord.ext import commands
from discord import app_commands

class TicketActionBarView(discord.ui.View):
    def __init__(self, bot, creator_id):
        super().__init__(timeout=None)
        self.bot, self.creator_id, self.claimed_by = bot, creator_id, None

    @discord.ui.button(label="Claim Ticket", style=discord.ButtonStyle.primary, custom_id="claim_btn", emoji="🙋‍♂️")
    async def claim_click(self, interaction: discord.Interaction, button: discord.ui.Button):
        async with self.bot.db.execute("SELECT staff_role_id FROM ticket_config WHERE guild_id=?", (interaction.guild_id,)) as c:
            row = await c.fetchone()
        staff_id = row[0] if row else None
        
        if staff_id and discord.utils.get(interaction.user.roles, id=staff_id) is None and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ Staff only.", ephemeral=True)
        if self.claimed_by:
            return await interaction.response.send_message(f"⚠️ Claimed by {self.claimed_by.mention}", ephemeral=True)

        self.claimed_by = interaction.user
        button.disabled, button.label, button.style = True, "Ticket Claimed", discord.ButtonStyle.secondary
        
        overwrites = interaction.channel.overwrites
        creator = interaction.guild.get_member(self.creator_id)
        if creator:
            overwrites[creator] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        if staff_id:
            s_role = interaction.guild.get_role(staff_id)
            if s_role: overwrites[s_role] = discord.PermissionOverwrite(view_channel=True, send_messages=False)
        overwrites[interaction.user] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        
        await interaction.channel.edit(overwrites=overwrites)
        await interaction.response.edit_message(view=self)
        await interaction.channel.send(embed=discord.Embed(description=f"🔹 Claimed by {interaction.user.mention}", color=0x3b82f6))

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, custom_id="close_btn", emoji="🔒")
    async def close_click(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel, guild = interaction.channel, interaction.guild
        async with self.bot.db.execute("SELECT log_channel_id FROM ticket_config WHERE guild_id=?", (interaction.guild_id,)) as c:
            row = await c.fetchone()
        log_id = row[0] if row else None

        await interaction.response.send_message("🔒 **Archiving and compiling HTML transcripts...**")
        transcript = await chat_exporter.export(channel)
        if not transcript: return await channel.send("❌ Transcript failed.")

        f_log = discord.File(io.BytesIO(transcript.encode()), filename=f"transcript-{channel.name}.html")
        f_dm = discord.File(io.BytesIO(transcript.encode()), filename=f"transcript-{channel.name}.html")
        creator = guild.get_member(self.creator_id)

        if creator:
            try:
                embed = discord.Embed(title="📜 TICKET SUMMARY", description=f"Closed in **{guild.name}**", color=0xD4AF37)
                embed.add_field(name="Channel", value=f"`{channel.name}`").add_field(name="Staff", value=self.claimed_by.mention if self.claimed_by else "None")
                await creator.send(embed=embed, file=f_dm)
            except: pass

        if log_id:
            log_chan = guild.get_channel(log_id)
            if log_chan:
                embed = discord.Embed(title="🔴 Ticket Closed", color=0xef4444, timestamp=interaction.created_at)
                embed.add_field(name="Channel", value=channel.name).add_field(name="User", value=f"<@{self.creator_id}>").add_field(name="Staff", value=interaction.user.mention)
                await log_chan.send(embed=embed, file=f_log)

        await asyncio.sleep(5)
        try: await channel.delete()
        except: pass

class TicketPanelSelect(discord.ui.Select):
    def __init__(self, config):
        self.config = config
        options = [
            discord.SelectOption(label="General Support", emoji="❓", value="general"),
            discord.SelectOption(label="Payment & Premium", emoji="💰", value="payment"),
            discord.SelectOption(label="Report Player", emoji="🛡️", value="report")
        ]
        super().__init__(placeholder="Select topic...", options=options, custom_id="tk_drop")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(TicketModal(self.config, self.values[0]))

class TicketCreationReasonModal(discord.ui.Modal, title="Open Support Ticket"):
    # Fallback initialization mapping compatibility
    def __init__(self, config, ticket_type):
        super().__init__()
        self.config, self.ticket_type = config, ticket_type

class TicketModal(discord.ui.Modal, title="Open Support Ticket"):
    reason = discord.ui.TextInput(label="Reason for ticket:", style=discord.TextStyle.paragraph, required=True)
    def __init__(self, config, ticket_type):
        super().__init__()
        self.config, self.ticket_type = config, ticket_type

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        cat_id = self.config[1] if self.config else None
        staff_id = self.config[2] if self.config else None
        log_id = self.config[3] if self.config else None

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        }
        if staff_id:
            s_role = guild.get_role(staff_id)
            if s_role: overwrites[s_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

        cat = guild.get_channel(cat_id) if cat_id else None
        chan = await guild.create_text_channel(name=f"{self.ticket_type}-{interaction.user.name}", category=cat, overwrites=overwrites)
        
        embed = discord.Embed(title=f"🎫 Ticket: {self.ticket_type.upper()}", description=f"Welcome {interaction.user.mention}\n**Reason:** {self.reason.value}", color=0x3b82f6)
        await chan.send(content=interaction.user.mention, embed=embed, view=TicketActionBarView(interaction.client, interaction.user.id))
        await interaction.followup.send(f"✅ Ticket opened: {chan.mention}", ephemeral=True)

        if log_id:
            l_chan = guild.get_channel(log_id)
            if l_chan:
                embed = discord.Embed(title="🟢 Ticket Created", color=0x10b981).add_field(name="User", value=interaction.user.mention).add_field(name="Channel", value=chan.mention)
                await l_chan.send(embed=embed)

class ProfessionalTickets(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @app_commands.command(name="setup-tickets", description="Launch ticket panel.")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_tickets(self, interaction: discord.Interaction, target_channel: discord.TextChannel, ticket_category: discord.CategoryChannel, staff_role: discord.Role, log_channel: discord.TextChannel):
        await interaction.response.defer(ephemeral=True)
        async with self.bot.db.cursor() as cur:
            await cur.execute("INSERT INTO ticket_config VALUES (?,?,?,?) ON CONFLICT(guild_id) DO UPDATE SET ticket_category_id=excluded.ticket_category_id, staff_role_id=excluded.staff_role_id, log_channel_id=excluded.log_channel_id", (interaction.guild_id, ticket_category.id, staff_role.id, log_channel.id))
        await self.bot.db.commit()
        async with self.bot.db.execute("SELECT * FROM ticket_config WHERE guild_id=?", (interaction.guild_id,)) as c:
            config = await c.fetchone()

        embed = discord.Embed(title="🎫 Premium Help Desk", description="Select topic below to open ticket.", color=0x3b82f6)
        view = discord.ui.View(timeout=None)
        view.add_item(TicketPanelSelect(config))
        await target_channel.send(embed=embed, view=view)
        await interaction.followup.send("✅ Configured!", ephemeral=True)

async def setup(bot): await bot.add_cog(ProfessionalTickets(bot))
      
