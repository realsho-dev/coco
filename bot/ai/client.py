import os
from dotenv import load_dotenv
from together import Together

# Load API key and initialize Together client
load_dotenv()
client = Together(api_key=os.getenv("TOGETHER_API_KEY"))
BOT_PREFIX = os.getenv("BOT_PREFIX", ".")  # Default to '.' if not set

# Get response from Together AI
def get_ai_response(prompt, context=""):
    try:
        system_prompt = (
            "You are a helpful Discord bot named coco, created by Ayanokouji. "
            "You answer shortly and clearly. Use recent messages and user info to personalize your response."
        )
        full_prompt = f"{system_prompt}\n\nRecent context:\n{context}\n\nUser's message: {prompt}"

        response = client.chat.completions.create(
            model="meta-llama/Llama-3-70b-chat-hf",
            messages=[{"role": "user", "content": full_prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {e}"

# Get recent messages and build context with usernames and user IDs
async def build_context(channel, target_user, limit=50):
    try:
        messages = await channel.history(limit=limit).flatten()

        # Extract last 5 from chat (with author info)
        recent_chat = [
            f"{msg.author.name} ({msg.author.id}): {msg.content}"
            for msg in messages[:5]
        ]

        # Extract last 5 messages from the target user
        user_msgs = [
            f"{msg.author.name} ({msg.author.id}): {msg.content}"
            for msg in messages if msg.author == target_user
        ][:5]

        user_context = "\n".join(user_msgs)
        chat_context = "\n".join(recent_chat)

        return f"User info:\n{target_user.name} ({target_user.id})\n\nUser's past messages:\n{user_context}\n\nRecent chat:\n{chat_context}"
    except Exception as e:
        print(f"Context error: {e}")
        return ""

# Final bot message handler
async def handle_discord_message(message, prefix='-ask'):
    # Ignore if not in aichannel
    if message.channel.name != "aichannel":
        return

    # Ignore messages from bots
    if message.author.bot:
        return

    # Ignore all messages starting with BOT_PREFIX
    if message.content.startswith(BOT_PREFIX):
        return

    # Check if message starts with -ask
    if message.content.startswith(prefix):
        user_input = message.content[len(prefix):].strip()
    elif message.reference:
        # Check if it is replying to a message that had -ask
        try:
            ref = await message.channel.fetch_message(message.reference.message_id)
            if not ref.content.startswith(prefix):
                return
            user_input = message.content.strip()
            context_msg = f"Replied to: {ref.author.name} - {ref.content}"
        except:
            return
    else:
        # For .aichannel mode - respond to all messages that don't start with BOT_PREFIX
        user_input = message.content.strip()

    # Build context and send to AI
    context_msg = ""
    if message.reference:
        try:
            ref = await message.channel.fetch_message(message.reference.message_id)
            context_msg = f"Replied to: {ref.author.name} - {ref.content}"
        except:
            pass

    user_context = await build_context(message.channel, message.author)
    full_context = f"{context_msg}\n{user_context}".strip()

    reply = get_ai_response(user_input, full_context)
    await message.channel.send(reply)