import os
import discord
from discord.ext import commands
import aiosqlite
import chat_exporter
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

class PublicUltimateBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='.', intents=intents, help_command=None)
        self.db = None

    async def setup_hook(self):
        # Database architecture supporting independent multi-server settings
        self.db = await aiosqlite.connect("database.db")
        async with self.db.cursor() as cursor:
            # Verification Settings Table
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS verify_config (
                    guild_id INTEGER PRIMARY KEY,
                    unverified_role_id INTEGER,
                    verified_role_id INTEGER
                )
            """)
            # Tickets Settings Table
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS ticket_config (
                    guild_id INTEGER PRIMARY KEY,
                    ticket_category_id INTEGER,
                    staff_role_id INTEGER,
                    log_channel_id INTEGER
                )
            """)
        await self.db.commit()
        print("📁 SQLite Public Database Core Initialized.")
        
        # Load Cog Extension Subdirectories
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                await self.load_extension(f'cogs.{filename[:-3]}')
                print(f"Loaded Extension Module: cogs.{filename[:-3]}")
        
        # ⚡ INSTANT SERVER REFRESH BYPASS SYSTEM ⚡
        # Replace the number below with your actual testing server ID
        TEST_GUILD_ID =  1554538660735746051 
        
        print(f"🔄 Copying global command matrices directly into server: {TEST_GUILD_ID}...")
        guild_target = discord.Object(id=TEST_GUILD_ID)
        self.tree.copy_global_to(guild=guild_target)
        await self.tree.sync(guild=guild_target)
        print("⚡ Guild-specific fast-sync sequence completed. Commands are now live inside your testing server!")

bot = PublicUltimateBot()

@bot.event
async def on_ready():
    print(f"🤖 Bot is fully live as {bot.user}")
    chat_exporter.init_exporter(bot)
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="over Public Servers"))

import asyncio
async def main():
    async with bot:
        await bot.start(os.getenv("DISCORD_TOKEN"))

if __name__ == "__main__":
    asyncio.run(main())
  
