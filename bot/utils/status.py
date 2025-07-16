import discord
import asyncio

async def update_status(bot):
    while True:
        # Single status message showing help command
        help_command = f"{bot.command_prefix}help" if hasattr(bot, 'command_prefix') else "/help"
        activity = discord.Activity(
            type=discord.ActivityType.listening,
            name=f"{help_command}"
        )
        await bot.change_presence(activity=activity)
        await asyncio.sleep(60)  # Update every 60 seconds instead of 20