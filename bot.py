import os
import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
import chat_exporter
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

class AdvancedBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='.', intents=intents, help_command=None)
        self.db = None

    async def setup_hook(self):
        # Establish database tables with additional columns for tracking panel options
        self.db = await aiosqlite.connect("database.db")
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS server_config (
                    guild_id INTEGER PRIMARY KEY,
                    unverified_role_id INTEGER,
                    verified_role_id INTEGER,
                    ticket_category_id INTEGER,
                    log_channel_id INTEGER
                )
            """)
        await self.db.commit()
        print("📁 SQLite Database connected securely.")
        
        # Load extensions
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                await self.load_extension(f'cogs.{filename[:-3]}')
        
        # Sync slash commands globally
        await self.tree.sync()
        print("⚡ Slash Commands synced globally across public environments.")

bot = AdvancedBot()

@bot.event
async def on_ready():
    print(f"🤖 Public Advanced Bot online as {bot.user}")
    chat_exporter.init_exporter(bot)
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Tickets & Transcripts"))

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return
    message.content = message.content.lower()
    await bot.process_commands(message)

import asyncio
async def main():
    async with bot:
        await bot.start(os.getenv("DISCORD_TOKEN"))

if __name__ == "__main__":
    asyncio.run(main())
      
