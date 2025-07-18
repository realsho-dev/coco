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
BOT_PREFIX = '-'  # Changed to - as you asked

def get_ai_response(prompt, context=""):
    try:
        system_prompt = textwrap.dedent(f"""
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
        {BOT_PREFIX}kick @user [reason] - Kick a user
        {BOT_PREFIX}ban @user [reason] - Ban a user
        {BOT_PREFIX}unban user_id - Unban a user
        {BOT_PREFIX}timeout @user 10s/m/h - Timeout a user
        {BOT_PREFIX}untimeout @user - Remove timeout
        {BOT_PREFIX}warn @user [reason] - Warn a user
        {BOT_PREFIX}warnings @user - Check user warnings
        {BOT_PREFIX}clearwarnings @user - Clear all warnings
        {BOT_PREFIX}purge 2 - Purge messages
        {BOT_PREFIX}snipe - Show last deleted message
        {BOT_PREFIX}lock #channel - Lock a channel
        {BOT_PREFIX}unlock #channel - Unlock a channel
        {BOT_PREFIX}slowmode #channel 10s/m/h - Set slowmode
        {BOT_PREFIX}hide #channel - Hide a channel
        {BOT_PREFIX}unhide #channel - Unhide a channel
        {BOT_PREFIX}nuke #channel - Nuke a channel
        {BOT_PREFIX}addrole @user @role - Add role
        {BOT_PREFIX}removerole @user @role - Remove role
        {BOT_PREFIX}addemoji :emoji: - Add emoji

        Utility commands:
        {BOT_PREFIX}ping - Show latency
        {BOT_PREFIX}uptime - Show uptime
        {BOT_PREFIX}help - Help menu
        {BOT_PREFIX}userinfo @user - User info
        {BOT_PREFIX}avatar @user - Show avatar
        {BOT_PREFIX}serverinfo - Server info
        {BOT_PREFIX}roleinfo @role - Role info
        {BOT_PREFIX}emojis - Show emojis
        {BOT_PREFIX}boosts - Server boosts
        {BOT_PREFIX}say Hello - Repeat text
        {BOT_PREFIX}remindme 10m Take a break - Set reminder
        {BOT_PREFIX}invite - Bot invite
        {BOT_PREFIX}support - Support server
        {BOT_PREFIX}suggest - Suggestion for the developer

        AI Commands:
        {BOT_PREFIX}aichannel #channel - Set AI channel
        {BOT_PREFIX}ask What is AI? - Ask AI
        {BOT_PREFIX}clearhistory - Clear AI chat
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
    conversation_history[channel_id] = conversation_history[channel_id][-MAX_HISTORY:]

async def get_history(channel_id):
    return "\n".join(conversation_history.get(channel_id, ["No history yet"]))

# Single handler, only responds in 'aichannel' to non-command messages
async def handle_discord_message(message):
    # Only in aichannel, only if not from bot
    if message.channel.name.lower() != "aichannel" or message.author.bot:
        return

    # Ignore command messages (like -ask, -help, etc)
    if message.content.startswith(BOT_PREFIX):
        return

    await update_history(message.channel.id, message.author, message.content)

    async with message.channel.typing():
        history = await get_history(message.channel.id)
        reply = get_ai_response(message.content, history)
        sent_message = await message.channel.send(reply)
        await update_history(message.channel.id, sent_message.author, reply, is_bot=True)
