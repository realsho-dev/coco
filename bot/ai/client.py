import os
from dotenv import load_dotenv
from together import Together
import textwrap
import asyncio

# Conversation history
conversation_history = {}
MAX_HISTORY = 5  # Last 5 messages stored

load_dotenv()
client = Together(api_key=os.getenv("TOGETHER_API_KEY"))
BOT_PREFIX = '-'  # Command prefix

def get_ai_response(prompt, context=""):
    try:
        system_prompt = textwrap.dedent(f"""
        About Yourself:
        1. You are Coco, a helpful AI assistant.
        2. You can answer questions, provide info, and assist with tasks.
        3. You are friendly, short, and professional.
        4. You are developed by Ayanokouji.

        Response Rules:
        1. Be short but helpful (1-3 lines)
        2. Use past chat (conversation history)
        3. For next questions, continue naturally

        Bot Commands:

        Moderation:
        {BOT_PREFIX}kick @user [reason]
        {BOT_PREFIX}ban @user [reason]
        {BOT_PREFIX}unban user_id
        {BOT_PREFIX}timeout @user 10s/m/h
        {BOT_PREFIX}untimeout @user
        {BOT_PREFIX}warn @user [reason]
        {BOT_PREFIX}warnings @user
        {BOT_PREFIX}clearwarnings @user
        {BOT_PREFIX}purge 2
        {BOT_PREFIX}snipe
        {BOT_PREFIX}lock #channel
        {BOT_PREFIX}unlock #channel
        {BOT_PREFIX}slowmode #channel 10s/m/h
        {BOT_PREFIX}hide #channel
        {BOT_PREFIX}unhide #channel
        {BOT_PREFIX}nuke #channel
        {BOT_PREFIX}addrole @user @role
        {BOT_PREFIX}removerole @user @role
        {BOT_PREFIX}addemoji :emoji:

        Utility:
        {BOT_PREFIX}ping
        {BOT_PREFIX}uptime
        {BOT_PREFIX}help
        {BOT_PREFIX}userinfo @user
        {BOT_PREFIX}avatar @user
        {BOT_PREFIX}serverinfo
        {BOT_PREFIX}roleinfo @role
        {BOT_PREFIX}emojis
        {BOT_PREFIX}boosts
        {BOT_PREFIX}say Hello
        {BOT_PREFIX}remindme 10m Take a break
        {BOT_PREFIX}invite
        {BOT_PREFIX}support
        {BOT_PREFIX}suggest

        AI:
        {BOT_PREFIX}aichannel #channel
        {BOT_PREFIX}ask What is AI?
        {BOT_PREFIX}clearhistory
        """).strip()

        full_context = textwrap.dedent(f"""
        === CHAT HISTORY ===
        {context}

        === NEW MESSAGE ===
        {prompt}
        """).strip()

        response = client.chat.completions.create(
            model="meta-llama/Llama-3-70b-chat-hf",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "assistant", "content": context if context else "New chat started"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"AI Error: {e}")
        return "Oops! Something went wrong."

# Update conversation history
async def update_history(channel_id, author, message, is_bot=False):
    if channel_id not in conversation_history:
        conversation_history[channel_id] = []

    prefix = "🤖 Coco" if is_bot else f"👤 {author.display_name}"
    entry = f"{prefix}: {message}"
    conversation_history[channel_id].append(entry)
    conversation_history[channel_id] = conversation_history[channel_id][-MAX_HISTORY:]

async def get_history(channel_id):
    return "\n".join(conversation_history.get(channel_id, ["No history yet"]))


# 🚫 Avoid double replies, especially with -ask and replies
async def handle_discord_message(message):
    # Skip if not in 'aichannel' or is a bot
    if message.channel.name.lower() != "aichannel" or message.author.bot:
        return

    # 🚫 Skip if message is a reply to bot (avoid double response)
    if message.reference:
        try:
            replied_message = await message.channel.fetch_message(message.reference.message_id)
            if replied_message and replied_message.author.bot:
                return
        except:
            pass  # just in case reply fetch fails

    # 🚫 Skip commands like -ask, -help, etc.
    if message.content.startswith(BOT_PREFIX):
        return

    # Update history with user message
    await update_history(message.channel.id, message.author, message.content)

    async with message.channel.typing():
        history = await get_history(message.channel.id)
        reply = get_ai_response(message.content, history)
        sent = await message.channel.send(reply)
        await update_history(message.channel.id, sent.author, reply, is_bot=True)
