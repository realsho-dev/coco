# main.py
import asyncio
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

# Start the dummy health check server
import healthcheck
healthcheck.start()

# Importing the setup functions for each command category
from bot.commands.moderation import setup_moderation
from bot.commands.utility import setup_utility
from bot.commands.ai import setup_ai
from bot.commands.help import setup_help  # Ensure this exists and is correct
from bot.utils.status import update_status

# Load environment variables from .env file
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
PREFIX = os.getenv("BOT_PREFIX", ".")

# Set up intents for the bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

# Create bot instance
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

async def setup_bot():
    # Remove default help command and set up all command categories
    bot.remove_command("help")  # Ensure this is before adding your custom help
    setup_moderation(bot)
    setup_utility(bot)
    setup_ai(bot)
    setup_help(bot)  # Ensure this correctly sets up your custom help

    @bot.event
    async def on_ready():
        print(f"Bot online as {bot.user}")
        await bot.tree.sync()  # Sync slash commands
        print("Slash commands synced")
        bot.loop.create_task(update_status(bot))  # Start updating bot status

    # Start the bot using the token from the .env file
    await bot.start(TOKEN)

# This condition ensures the script runs when directly executed
if __name__ == "__main__":
    asyncio.run(setup_bot())