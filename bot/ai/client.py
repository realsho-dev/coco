import os
from dotenv import load_dotenv
from together import Together
import textwrap
import asyncio

# Conversation history storage
conversation_history = {}
MAX_HISTORY = 5  # Keep last 5 messages per channel

load_dotenv()
client = Together(api_key=os.getenv("TOGETHER_API_KEY"))
BOT_PREFIX = os.getenv("BOT_PREFIX", ".")

def get_ai_response(prompt, context=""):
    try:
        system_prompt = textwrap.dedent("""
        About Yourself:
        1. You are Coco, a helpful AI assistant.
        2. You can answer questions, provide information, and assist with tasks.
        3. You are friendly, concise, and professional. 
        4. You are developed by Ayanokouji.
        
                                        
        Response Guidelines:
        1. Be concise but helpful (1-3 sentences usually)
        2. Remember the conversation history
        3. For follow-up questions, continue naturally
                                        
        Additional Information:
        You are a moderation and utilities bot along with the AI assistant.
        
        Moderation commands:
        {prefix}kick @user [reason] - Kick a user
{prefix}ban @user [reason] - Ban a user  
{prefix}unban user_id - Unban a user
{prefix}timeout @user 10s/m/h - Timeout a user
{prefix}untimeout @user - Remove timeout
{prefix}warn @user [reason] - Warn a user
{prefix}warnings @user - Check user warnings
{prefix}clearwarnings @user - Clear all warnings
{prefix}purge 2 - Purge messages
{prefix}snipe - Show last deleted message
{prefix}lock #channel - Lock a channel
{prefix}unlock #channel - Unlock a channel  
{prefix}slowmode #channel 10s/m/h - Set slowmode
{prefix}hide #channel - Hide a channel
{prefix}unhide #channel - Unhide a channel
{prefix}nuke #channel - Nuke a channel
{prefix}addrole @user @role - Add role
{prefix}removerole @user @role - Remove role
{prefix}addemoji :emoji: - Add emoji
                                        
        Utility commands:
        {prefix}ping - Show latency  
{prefix}uptime - Show uptime
{prefix}help - Help menu
{prefix}userinfo @user - User info
{prefix}avatar @user - Show avatar  
{prefix}serverinfo - Server info
{prefix}roleinfo @role - Role info
{prefix}emojis - Show emojis
{prefix}boosts - Server boosts
{prefix}say Hello - Repeat text
{prefix}remindme 10m Take a break - Set reminder
{prefix}invite - Bot invite
{prefix}support - Support server
{prefix}suggest - Suggestion for the developer
                                        

    AI Commands:
                                        {prefix}aichannel #channel - Set AI channel  
{prefix}ask What is AI? - Ask AI
{prefix}clearhistory - Clear AI chat
        """).strip()
        
        full_context = textwrap.dedent(f"""
        === CONVERSATION HISTORY ===
        {context}
        
        === NEW MESSAGE ===
        {prompt}
        """).strip()

        response = client.chat.completions.create(
            model="meta-llama/Llama-3-70b-chat-hf",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "assistant", "content": context if context else "New conversation started"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"AI Error: {e}")
        return "Oops! Let me try that again... 🔄"

async def update_history(channel_id, author, message, is_bot=False):
    if channel_id not in conversation_history:
        conversation_history[channel_id] = []
    
    prefix = "🤖 Coco" if is_bot else f"👤 {author.display_name}"
    entry = f"{prefix}: {message}"
    
    conversation_history[channel_id].append(entry)
    # Keep only the most recent messages
    conversation_history[channel_id] = conversation_history[channel_id][-MAX_HISTORY:]

async def get_history(channel_id):
    return "\n".join(conversation_history.get(channel_id, ["No history yet"]))

async def handle_discord_message(message):
    # Ignore if not in aichannel or from bots
    if message.channel.name.lower() != "aichannel" or message.author.bot:
        return
    
    # Update history with user message
    await update_history(message.channel.id, message.author, message.content)
    
    # Always respond (not just to replies)
    async with message.channel.typing():
        # Get conversation history
        history = await get_history(message.channel.id)
        
        # Get AI response
        reply = get_ai_response(message.content, history)
        
        # Send response and update history with bot's message
        sent_message = await message.channel.send(reply)
        await update_history(message.channel.id, sent_message.author, reply, is_bot=True)

# In your bot setup, use this handler instead of the previous one
async def handle_discord_message(message):
    # Ignore if not in aichannel or from bots
    if message.channel.name.lower() != "aichannel" or message.author.bot:
        return
    
    # List of command prefixes to ignore
    BOT_COMMAND_PREFIXES = ['.', '!', '?', '-']  # Add any prefixes you use
    
    # Check if message starts with any command prefix
    if any(message.content.startswith(prefix) for prefix in BOT_COMMAND_PREFIXES):
        return
    
    # Rest of your existing handling code...
    await update_history(message.channel.id, message.author, message.content)
    
    async with message.channel.typing():
        history = await get_history(message.channel.id)
        reply = get_ai_response(message.content, history)
        sent_message = await message.channel.send(reply)
        await update_history(message.channel.id, sent_message.author, reply, is_bot=True)