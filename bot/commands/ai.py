from discord.ext import commands
import discord
from bot.ai.client import get_ai_response

ai_channel = None
chat_history = []

def setup_ai(bot):
    @bot.event
    async def on_message(message):
        if message.author.bot:
            return

        # Don't trigger AI in DMs or without channel
        if not message.guild or not message.channel:
            return

        # Check if message is in AI channel or is a reply containing -ask
        is_ai_channel = ai_channel and message.channel.id == ai_channel
        is_ask_reply = message.reference and '-ask' in message.content

        if is_ai_channel or is_ask_reply:
            # Get context from replied message if exists
            context = None
            if message.reference:
                try:
                    replied_message = await message.channel.fetch_message(message.reference.message_id)
                    context = replied_message.content
                except:
                    pass

            # For AI channel, store in history
            if is_ai_channel:
                chat_history.append(f"{message.author.name}: {message.content}")
                if len(chat_history) > 10:
                    chat_history.pop(0)

            # Remove -ask from prompt if present
            prompt = message.content.replace('-ask', '').strip()
            
            # Get AI response with context
            response = get_ai_response(prompt, context)
            
            # Reply to the message
            await message.reply(response)

        # Process commands normally
        if message.content.startswith(bot.command_prefix):
            await bot.process_commands(message)

    @bot.hybrid_command(name="ask")
    async def ask(ctx: commands.Context, *, question: str = None):
        if not question:
            await ctx.send(embed=discord.Embed(
                title="Error",
                description=f"Use `{bot.command_prefix}ask <question>`",
                color=0xCD5C5C
            ))
            return

        # Check if this is a reply to get context
        context = None
        if ctx.message.reference:
            try:
                replied_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
                context = replied_message.content
            except:
                pass

        prompt = f"{ctx.author.name}: {question}\nAnswer concisely:"
        response = get_ai_response(prompt, context)
        await ctx.send(response)

    @bot.hybrid_command(name="aichannel")
    @commands.has_permissions(manage_channels=True)
    async def set_ai_channel(ctx: commands.Context, channel: discord.TextChannel = None):
        global ai_channel
        target_channel = channel or ctx.channel

        # Toggle behavior - if same channel is specified, disable AI
        if ai_channel == target_channel.id:
            ai_channel = None
            embed = discord.Embed(
                title="❌ AI Channel Disabled",
                description=f"AI responses have been **disabled** in {target_channel.mention}",
                color=0xFF0000
            )
        else:
            ai_channel = target_channel.id
            embed = discord.Embed(
                title="✅ AI Channel Enabled",
                description=f"AI responses are now **active** in {target_channel.mention}\n\n"
                           f"• Just type normally to chat with the AI\n"
                           f"• Or use `{bot.command_prefix}ask` in other channels\n"
                           f"• Always reply to AI's message for more personalized context",
                color=0x00FF00
            )

        await ctx.send(embed=embed)

    @bot.hybrid_command(name="clearhistory")
    async def clearhistory(ctx: commands.Context):
        global chat_history
        chat_history = []
        await ctx.send(embed=discord.Embed(
            title="History Cleared",
            description="AI chat history reset",
            color=0x9ACD32
        ))