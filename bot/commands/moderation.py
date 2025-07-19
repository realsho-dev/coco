import discord
from discord.ext import commands
import asyncio
import aiohttp
import typing
from datetime import timedelta
import re

intents = discord.Intents.all()  # Needed for moderation bots
bot = commands.Bot(command_prefix="/", intents=intents)  # Or your own prefix

# --- Global Variables and Configuration ---
log_channel = None  # Channel ID where moderation actions will be logged
warnings_db = {}  # In-memory warnings (as a dictionary)
last_deleted_message = None  # Stores the last deleted message for the snipe command

# --- Helper Function for Logging Moderator Actions ---
async def log_action(bot, action, target, reason, moderator, extra_info=""):
    if log_channel:
        channel = bot.get_channel(log_channel)
        if channel:
            embed = discord.Embed(
                title=f"Log: {action}",
                description=f"Target: {target}\nReason: {reason or 'No reason given'}\nBy: {moderator}\n{extra_info}",
                color=0x708090
            )
            await channel.send(embed=embed)

def setup_moderation(bot):
    # --- Moderation Commands ---

    @bot.hybrid_command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick(ctx, member: discord.Member, *, reason: str = None):
        try:
            await member.kick(reason=reason)
            await ctx.send(f"✅ **Success:** {member.display_name} has been kicked.\n**Reason:** {reason or 'No reason given'}.")
            await log_action(bot, "Kick", member.display_name, reason, ctx.author)
        except discord.Forbidden:
            await ctx.send("❌ **Error:** I do not have permission to kick this user. Please check my permissions.")
        except Exception as e:
            await ctx.send(f"⚠️ **Error:** Something went wrong. Please try again later.\n**Error:** {e}")

    @bot.hybrid_command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban(ctx, member: discord.Member, *, reason: str = None):
        try:
            await member.ban(reason=reason)
            await ctx.send(f"✅ **Success:** {member.display_name} has been banned.\n**Reason:** {reason or 'No reason given'}.")
            await log_action(bot, "Ban", member.display_name, reason, ctx.author)
        except discord.Forbidden:
            await ctx.send("❌ **Error:** I do not have permission to ban this user. Please check my permissions.")
        except Exception as e:
            await ctx.send(f"⚠️ **Error:** Something went wrong. Please try again later.\n**Error:** {e}")

    @bot.hybrid_command(name="unban")
    @commands.has_permissions(ban_members=True)
    async def unban(ctx, *, user: str):
        try:
            banned_users = await ctx.guild.bans()
            name, discriminator = (user.split("#") if "#" in user else (user, None))

            for ban_entry in banned_users:
                if ban_entry.user.name == name and (discriminator is None or ban_entry.user.discriminator == discriminator):
                    await ctx.guild.unban(ban_entry.user)
                    await ctx.send(f"✅ **Success:** {user} was unbanned and can join again.")
                    await log_action(bot, "Unban", user, "Manual Unban", ctx.author)
                    return
            await ctx.send("❌ **Error:** User not found in ban list or format is incorrect. Use `name#discriminator` or just name.")
        except Exception as e:
            await ctx.send(f"⚠️ **Error:** Could not unban. Error: {e}")

    @bot.hybrid_command(name="timeout")
    @commands.has_permissions(moderate_members=True)
    async def timeout(ctx, member: discord.Member, duration: str):
        try:
            seconds = 0
            if duration.endswith('s'):
                seconds = int(duration[:-1])
            elif duration.endswith('m'):
                seconds = int(duration[:-1]) * 60
            elif duration.endswith('h'):
                seconds = int(duration[:-1]) * 3600
            else:
                seconds = int(duration)
            await member.timeout(discord.utils.utcnow() + timedelta(seconds=seconds))
            await ctx.send(f"✅ **Success:** {member.display_name} is timed out for {duration}. They cannot send messages now.")
            await log_action(bot, "Timeout", member.display_name, duration, ctx.author)
        except ValueError:
            await ctx.send("❌ **Error:** Invalid duration format. Use like `30s` (seconds), `5m` (minutes), or `1h` (hours).")
        except discord.Forbidden:
            await ctx.send("❌ **Error:** I do not have permission to timeout this member.")
        except Exception as e:
            await ctx.send(f"⚠️ **Error:** Something went wrong. Please try again later. Error: {e}")

    @bot.hybrid_command(name="untimeout")
    @commands.has_permissions(moderate_members=True)
    async def untimeout(ctx, member: discord.Member):
        try:
            await member.timeout(None)
            await ctx.send(f"✅ **Success:** Timeout removed from {member.display_name}. They can talk again.")
            await log_action(bot, "Untimeout", member.display_name, "Timeout removed", ctx.author)
        except discord.Forbidden:
            await ctx.send("❌ **Error:** I do not have permission to remove timeout from this member.")
        except Exception as e:
            await ctx.send(f"⚠️ **Error:** Something went wrong. Please try again later. Error: {e}")

    @bot.hybrid_command(name="warn")
    @commands.has_permissions(manage_messages=True)
    async def warn(ctx, member: discord.Member, *, reason: str = "No reason given"):
        try:
            if member.id not in warnings_db:
                warnings_db[member.id] = []
            warnings_db[member.id].append(reason)
            await ctx.send(f"⚠️ **Warning:** {member.display_name} has been warned.\n**Reason:** {reason}.")
            await log_action(bot, "Warn", member.display_name, reason, ctx.author)
        except Exception as e:
            await ctx.send(f"⚠️ **Error:** Warning failed. Error: {e}")

    @bot.hybrid_command(name="warnings")
    async def warnings(ctx, member: discord.Member):
        try:
            warns = warnings_db.get(member.id, [])
            if not warns:
                await ctx.send(f"✅ **Info:** No warnings for {member.display_name}.")
            else:
                warn_list = "\n".join([f"- {w}" for w in warns])
                embed = discord.Embed(
                    title=f"Warnings for {member.display_name}",
                    description=warn_list,
                    color=discord.Color.orange()
                )
                await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"⚠️ **Error:** Could not check warnings. Error: {e}")

    @bot.hybrid_command(name="clearwarnings")
    @commands.has_permissions(manage_messages=True)
    async def clearwarnings(ctx, member: discord.Member):
        try:
            if member.id in warnings_db:
                warnings_db.pop(member.id)
                await ctx.send(f"🗑️ **Success:** All warnings cleared for {member.display_name}.")
                await log_action(bot, "Clear Warnings", member.display_name, "All warnings cleared", ctx.author)
            else:
                await ctx.send(f"✅ **Info:** No warnings found for {member.display_name} to clear.")
        except Exception as e:
            await ctx.send(f"⚠️ **Error:** Could not clear warnings. Error: {e}")

    @bot.hybrid_command(name="purge")
    @commands.has_permissions(manage_messages=True)
    async def purge(ctx, amount: int):
        if amount <= 0 or amount > 1000:
            return await ctx.send("❌ **Error:** Amount must be between 1 and 1000.")
        try:
            deleted_messages = await ctx.channel.purge(limit=amount + 1)
            msg = await ctx.send(f"🧹 **Success:** {len(deleted_messages) - 1} messages were removed by {ctx.author.display_name}.")
            await asyncio.sleep(3)
            await msg.delete()
        except discord.Forbidden:
            await ctx.send("❌ **Error:** I do not have permission to remove messages.")
        except Exception as e:
            await ctx.send(f"⚠️ **Error:** Could not remove messages. Error: {e}")

    @bot.hybrid_command(name="snipe")
    async def snipe(ctx):
        global last_deleted_message
        try:
            if last_deleted_message:
                embed = discord.Embed(
                    title="Sniped Message",
                    description=last_deleted_message.content,
                    color=discord.Color.blue()
                )
                embed.set_author(
                    name=last_deleted_message.author.display_name,
                    icon_url=last_deleted_message.author.avatar.url if last_deleted_message.author.avatar else None
                )
                embed.set_footer(text=f"Channel: #{last_deleted_message.channel.name}")
                await ctx.send(embed=embed)
            else:
                await ctx.send("ℹ️ **Info:** No recently deleted message to snipe.")
        except Exception as e:
            await ctx.send(f"⚠️ **Error:** Could not snipe. Error: {e}")

    @bot.event
    async def on_message_delete(message):
        global last_deleted_message
        last_deleted_message = message

    @bot.hybrid_command(name="lock")
    @commands.has_permissions(manage_channels=True)
    async def lock(ctx):
        try:
            await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
            await ctx.send("🔒 **Success:** Channel is now locked. Only staff can send messages here.")
            await log_action(bot, "Lock Channel", ctx.channel.name, "Channel locked", ctx.author)
        except discord.Forbidden:
            await ctx.send("❌ **Error:** I do not have permission to lock this channel.")
        except Exception as e:
            await ctx.send(f"⚠️ **Error:** Could not lock the channel. Error: {e}")

    @bot.hybrid_command(name="unlock")
    @commands.has_permissions(manage_channels=True)
    async def unlock(ctx):
        try:
            await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
            await ctx.send("🔓 **Success:** Channel is now unlocked. Everyone can send messages.")
            await log_action(bot, "Unlock Channel", ctx.channel.name, "Channel unlocked", ctx.author)
        except discord.Forbidden:
            await ctx.send("❌ **Error:** I do not have permission to unlock this channel.")
        except Exception as e:
            await ctx.send(f"⚠️ **Error:** Could not unlock the channel. Error: {e}")

    @bot.hybrid_command(name="slowmode")
    @commands.has_permissions(manage_channels=True)
    async def slowmode(ctx, seconds: int):
        if seconds < 0 or seconds > 21600:
            return await ctx.send("❌ **Error:** Slowmode must be between 0 and 21600 seconds (6 hours).")
        try:
            await ctx.channel.edit(slowmode_delay=seconds)
            await ctx.send(f"🐢 **Success:** Slowmode set to {seconds} seconds in this channel.")
            await log_action(bot, "Slowmode", ctx.channel.name, f"{seconds} seconds", ctx.author)
        except discord.Forbidden:
            await ctx.send("❌ **Error:** I do not have permission to set slowmode here.")
        except Exception as e:
            await ctx.send(f"⚠️ **Error:** Could not set slowmode. Error: {e}")

    @bot.hybrid_command(name="hide")
    @commands.has_permissions(manage_channels=True)
    async def hide(ctx):
        try:
            await ctx.channel.set_permissions(ctx.guild.default_role, view_channel=False)
            await ctx.send("👀 **Success:** Channel is now hidden. Only staff can see it.")
            await log_action(bot, "Hide Channel", ctx.channel.name, "Hidden from @everyone", ctx.author)
        except discord.Forbidden:
            await ctx.send("❌ **Error:** I do not have permission to hide this channel.")
        except Exception as e:
            await ctx.send(f"⚠️ **Error:** Could not hide the channel. Error: {e}")

    @bot.hybrid_command(name="unhide")
    @commands.has_permissions(manage_channels=True)
    async def unhide(ctx):
        try:
            await ctx.channel.set_permissions(ctx.guild.default_role, view_channel=True)
            await ctx.send("👁️ **Success:** Channel is now visible to everyone.")
            await log_action(bot, "Unhide Channel", ctx.channel.name, "Visible to @everyone", ctx.author)
        except discord.Forbidden:
            await ctx.send("❌ **Error:** I do not have permission to unhide this channel.")
        except Exception as e:
            await ctx.send(f"⚠️ **Error:** Could not unhide the channel. Error: {e}")

    @bot.hybrid_command(name="nuke")
    @commands.has_permissions(manage_channels=True)
    async def nuke(ctx):
        try:
            confirm = await ctx.send("⚠️ Are you sure you want to nuke this channel? React with ✅ to confirm.")
            await confirm.add_reaction("✅")

            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) == '✅' and reaction.message.id == confirm.id

            await bot.wait_for('reaction_add', check=check, timeout=30.0)

            user_mention = ctx.author.mention
            new_channel = await ctx.channel.clone()
            await ctx.channel.delete()

            embed = discord.Embed(description=f"💥 **Success:** Channel nuked by {user_mention}! All messages are gone.")
            embed.set_image(url="https://media.tenor.com/SChKroGIZO8AAAAC/explosion-mushroom-cloud.gif")
            await new_channel.send(embed=embed)
            await log_action(bot, "Channel Nuke", new_channel.name, "Channel recreated", ctx.author)

        except asyncio.TimeoutError:
            await ctx.send("❌ **Error:** Nuke cancelled. You did not confirm in time.")
        except discord.Forbidden:
            await ctx.send("❌ **Error:** I do not have permission to nuke this channel. Please check my channel permissions.")
        except Exception as e:
            await ctx.send(f"⚠️ **Error:** An error occurred during nuke: {e}")

    @bot.hybrid_command(name="addrole")
    @commands.has_permissions(manage_roles=True)
    async def addrole(ctx, member: discord.Member, role: discord.Role):
        try:
            await member.add_roles(role)
            await ctx.send(f"🎭 **Success:** Added `{role.name}` to {member.display_name}.")
            await log_action(bot, "Add Role", member.display_name, role.name, ctx.author)
        except discord.Forbidden:
            await ctx.send("❌ **Error:** I do not have permission to add that role.")
        except Exception as e:
            await ctx.send(f"⚠️ **Error:** Could not add role. Error: {e}")

    @bot.hybrid_command(name="removerole")
    @commands.has_permissions(manage_roles=True)
    async def removerole(ctx, member: discord.Member, role: discord.Role):
        try:
            await member.remove_roles(role)
            await ctx.send(f"🎭 **Success:** Removed `{role.name}` from {member.display_name}.")
            await log_action(bot, "Remove Role", member.display_name, role.name, ctx.author)
        except discord.Forbidden:
            await ctx.send("❌ **Error:** I do not have permission to remove that role.")
        except Exception as e:
            await ctx.send(f"⚠️ **Error:** Could not remove role. Error: {e}")

    @bot.hybrid_command(name="steal")
    @commands.has_permissions(manage_emojis=True)
    async def steal(
        ctx: commands.Context,
        emoji_or_url: str,
        name: typing.Optional[str] = None
    ):
        try:
            try:
                partial_emoji = await commands.PartialEmojiConverter().convert(ctx, emoji_or_url)

                if len(ctx.guild.emojis) >= ctx.guild.emoji_limit:
                    return await ctx.send("❌ **Error:** This server has reached its emoji limit.")

                emoji_bytes = await partial_emoji.read()
                new_emoji = await ctx.guild.create_custom_emoji(
                    name=partial_emoji.name,
                    image=emoji_bytes,
                    reason=f"Stolen by {ctx.author}"
                )
                await ctx.send(f"😀 **Success:** Emoji `{partial_emoji.name}` added to the server!")
                await log_action(bot, "Steal Emoji", new_emoji.name, "Stolen from another server", ctx.author)
                return
            except commands.PartialEmojiConversionFailure:
                if name is None:
                    return await ctx.send(
                        "❌ **Error:** For URLs, you must give a name also. Example: `/steal <url> <name>`"
                    )
                image_url = emoji_or_url

                if not image_url.startswith(('http://', 'https://')):
                    return await ctx.send("❌ **Error:** Please provide a valid HTTP or HTTPS image link.")

                if not re.match(r'^https?://.*\.(jpeg|jpg|gif|png)$', image_url, re.IGNORECASE):
                    return await ctx.send("❌ **Error:** Only .jpg, .jpeg, .png or .gif files are supported.")

                if not (2 <= len(name) <= 32):
                    return await ctx.send("❌ **Error:** Emoji name must be 2-32 characters.")

                if len(ctx.guild.emojis) >= ctx.guild.emoji_limit:
                    return await ctx.send("❌ **Error:** This server has reached its emoji limit.")

                async with aiohttp.ClientSession() as session:
                    async with session.get(image_url) as resp:
                        if resp.status != 200:
                            return await ctx.send(f"❌ **Error:** Failed to download image. Status code: {resp.status}")
                        if 'image' not in resp.headers.get('Content-Type', ''):
                            return await ctx.send("❌ **Error:** The provided link is not an image.")

                        image_data = await resp.read()
                        if len(image_data) > 256 * 1024:
                            return await ctx.send("❌ **Error:** Image is too big (max 256KB).")

                        new_emoji = await ctx.guild.create_custom_emoji(
                            name=name,
                            image=image_data,
                            reason=f"Added by {ctx.author} from URL"
                        )
                        await ctx.send(f"😀 **Success:** Emoji `{name}` added to the server!")
                        await log_action(bot, "Add Emoji", new_emoji.name, f"Added from URL: {image_url}", ctx.author)

        except discord.HTTPException as e:
            if e.code == 30008:
                await ctx.send("❌ **Error:** Emoji slots are full.")
            elif e.code == 50045:
                await ctx.send("❌ **Error:** Image format is not accepted. Try using a normal PNG, JPG or GIF.")
            else:
                await ctx.send(f"❌ **Error:** Discord error: {str(e)}")
        except Exception as e:
            await ctx.send(f"⚠️ **Error:** An unexpected error occurred: {str(e)}")

# --- GLOBAL ERROR HANDLER BELOW ---

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ **Error:** You do not have permission to use this command.")
    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.send("❌ **Error:** I do not have permission to do this. Please check my role or ask an admin for help.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ **Error:** Missing input. Usage: `{ctx.prefix}{ctx.command} {ctx.command.signature}`")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ **Error:** Wrong input. Please check your command values.")
    else:
        await ctx.send(f"⚠️ **Error:** {str(error)}")

# Don't forget to call setup_moderation()
setup_moderation(bot)

# If you run the bot yourself, uncomment and fill in your token