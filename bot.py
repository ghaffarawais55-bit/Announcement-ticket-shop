import os
import discord
from discord.ext import commands
import aiosqlite
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='.', intents=intents, help_command=None)

# Initialize asynchronous database storage for individual server configuration tracking
async def init_db():
    bot.db = await aiosqlite.connect("database.db")
    async with bot.db.cursor() as cursor:
        await cursor.execute("""
            CREATE TABLE IF NOT EXISTS server_config (
                guild_id INTEGER PRIMARY KEY,
                unverified_role_id INTEGER,
                verified_role_id INTEGER,
                ticket_category_id INTEGER
            )
        """)
    await bot.db.commit()
    print("📁 SQLite database initialized successfully.")

@bot.event
async def on_ready():
    await init_db()
    print(f"🤖 Public Python Bot online as {bot.user}")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="over public servers"))

# Redirect prefix variations automatically to lowcase handlers
@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return
    
    # Ensures commands like .QR work seamlessly exactly like .qr
    message.content = message.content.lower()
    await bot.process_commands(message)

async def load_extensions():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')

import asyncio
async def main():
    async with bot:
        await load_extensions()
        await bot.start(os.getenv("DISCORD_TOKEN"))

if __name__ == "__main__":
    asyncio.run(main())
  
