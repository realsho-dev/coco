import discord
from discord.ext import commands
import asyncio
import aiohttp
import typing
from datetime import timedelta
import re

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
                description=f"Target: {target}\nReason: {reason or 'None'}\nBy: {moderator}\n{extra_info}",
                color=0x708090
            )
            await channel.send(embed=embed)

def setup_moderation(bot):
    # --- Moderation Commands ---

    @bot.hybrid_command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick(ctx, member: discord.Member, *, reason: str = None):
        await member.kick(reason=reason)
        await ctx.send(f"Kicked {member.name} for: {reason or 'no reason'}")
        await log_action(bot, "Kick", member.name, reason, ctx.author)

    @bot.hybrid_command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban(ctx, member: discord.Member, *, reason: str = None):
        await member.ban(reason=reason)
        await ctx.send(f"Banned {member.name} for: {reason or 'no reason'}")
        await log_action(bot, "Ban", member.name, reason, ctx.author)

    @bot.hybrid_command(name="unban")
    @commands.has_permissions(ban_members=True)
    async def unban(ctx, *, user: str):
        banned_users = await ctx.guild.bans()
        if "#" in user:
            name, discriminator = user.split("#")
        else:
            name = user
            discriminator = None

        for ban_entry in banned_users:
            if ban_entry.user.name == name and (discriminator is None or ban_entry.user.discriminator == discriminator):
                await ctx.guild.unban(ban_entry.user)
                await ctx.send(f"Unbanned {user}")
                await log_action(bot, "Unban", user, "Manual Unban", ctx.author)
                return
        await ctx.send("User not found in ban list or incorrect format.")

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
            await ctx.send(f"Timed out {member.name} for {duration}")
            await log_action(bot, "Timeout", member.name, duration, ctx.author)
        except ValueError:
            await ctx.send("Invalid duration format. Use formats like '30s', '5m', or '1h'.")
        except discord.Forbidden:
            await ctx.send("I don't have permission to timeout that member.")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    @bot.hybrid_command(name="untimeout")
    @commands.has_permissions(moderate_members=True)
    async def untimeout(ctx, member: discord.Member):
        await member.timeout(None)
        await ctx.send(f"Removed timeout from {member.name}")
        await log_action(bot, "Untimeout", member.name, "Timeout removed", ctx.author)

    @bot.hybrid_command(name="warn")
    @commands.has_permissions(manage_messages=True)
    async def warn(ctx, member: discord.Member, *, reason: str = "No reason provided"):
        if member.id not in warnings_db:
            warnings_db[member.id] = []
        warnings_db[member.id].append(reason)
        await ctx.send(f"Warned {member.name}: {reason}")
        await log_action(bot, "Warn", member.name, reason, ctx.author)

    @bot.hybrid_command(name="warnings")
    async def warnings(ctx, member: discord.Member):
        warns = warnings_db.get(member.id, [])
        if not warns:
            await ctx.send(f"No warnings for {member.name}.")
        else:
            warn_list = "\n".join([f"- {w}" for w in warns])
            embed = discord.Embed(
                title=f"Warnings for {member.display_name}",
                description=warn_list,
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)

    @bot.hybrid_command(name="clearwarnings")
    @commands.has_permissions(manage_messages=True)
    async def clearwarnings(ctx, member: discord.Member):
        if member.id in warnings_db:
            warnings_db.pop(member.id)
            await ctx.send(f"Cleared all warnings for {member.name}.")
            await log_action(bot, "Clear Warnings", member.name, "All warnings cleared", ctx.author)
        else:
            await ctx.send(f"No warnings found for {member.name} to clear.")

    @bot.hybrid_command(name="purge")
    @commands.has_permissions(manage_messages=True)
    async def purge(ctx, amount: int):
        if amount <= 0 or amount > 1000:
            return await ctx.send("Amount must be between 1 and 1000.", ephemeral=True)
        deleted_messages = await ctx.channel.purge(limit=amount + 1)
        msg = await ctx.send(f"{len(deleted_messages) - 1} message(s) purged by {ctx.author.mention}.")
        await asyncio.sleep(3)
        await msg.delete()

    @bot.hybrid_command(name="snipe")
    async def snipe(ctx):
        global last_deleted_message
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
            await ctx.send("No recently deleted message to snipe.")

    @bot.event
    async def on_message_delete(message):
        global last_deleted_message
        last_deleted_message = message

    @bot.hybrid_command(name="lock")
    @commands.has_permissions(manage_channels=True)
    async def lock(ctx):
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
        await ctx.send("🔒 Channel locked.")

    @bot.hybrid_command(name="unlock")
    @commands.has_permissions(manage_channels=True)
    async def unlock(ctx):
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
        await ctx.send("🔓 Channel unlocked.")

    @bot.hybrid_command(name="slowmode")
    @commands.has_permissions(manage_channels=True)
    async def slowmode(ctx, seconds: int):
        if seconds < 0 or seconds > 21600:
            return await ctx.send("Slowmode must be between 0 and 21600 seconds (6 hours).")
        await ctx.channel.edit(slowmode_delay=seconds)
        await ctx.send(f"Set slowmode to {seconds} seconds.")
        await log_action(bot, "Slowmode", ctx.channel.name, f"{seconds} seconds", ctx.author)

    @bot.hybrid_command(name="hide")
    @commands.has_permissions(manage_channels=True)
    async def hide(ctx):
        await ctx.channel.set_permissions(ctx.guild.default_role, view_channel=False)
        await ctx.send("Channel hidden.")
        await log_action(bot, "Hide Channel", ctx.channel.name, "Hidden from @everyone", ctx.author)

    @bot.hybrid_command(name="unhide")
    @commands.has_permissions(manage_channels=True)
    async def unhide(ctx):
        await ctx.channel.set_permissions(ctx.guild.default_role, view_channel=True)
        await ctx.send("Channel visible.")
        await log_action(bot, "Unhide Channel", ctx.channel.name, "Visible to @everyone", ctx.author)

    @bot.hybrid_command(name="nuke")
    @commands.has_permissions(manage_channels=True)
    async def nuke(ctx):
        try:
            confirm = await ctx.send("Are you sure you want to nuke this channel? React with ✅ to confirm.")
            await confirm.add_reaction("✅")

            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) == '✅' and reaction.message.id == confirm.id

            await bot.wait_for('reaction_add', check=check, timeout=30.0)

            user_mention = ctx.author.mention
            new_channel = await ctx.channel.clone()
            await ctx.channel.delete()

            # FIX: Show GIF using an embed (not just a link)
            embed = discord.Embed(description=f"💥 Channel nuked by {user_mention}!")
            embed.set_image(url="https://media.tenor.com/SChKroGIZO8AAAAC/explosion-mushroom-cloud.gif")
            await new_channel.send(embed=embed)
            await log_action(bot, "Channel Nuke", new_channel.name, "Channel recreated", ctx.author)

        except asyncio.TimeoutError:
            await ctx.send("Nuke cancelled. You did not confirm in time.")
        except Exception as e:
            await ctx.send(f"An error occurred during nuke: {e}")

    @bot.hybrid_command(name="addrole")
    @commands.has_permissions(manage_roles=True)
    async def addrole(ctx, member: discord.Member, role: discord.Role):
        try:
            await member.add_roles(role)
            await ctx.send(f"✅ Added **{role.name}** to {member.mention}.")
            await log_action(bot, "Add Role", member.name, role.name, ctx.author)
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to add that role.")
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

    @bot.hybrid_command(name="removerole")
    @commands.has_permissions(manage_roles=True)
    async def removerole(ctx, member: discord.Member, role: discord.Role):
        try:
            await member.remove_roles(role)
            await ctx.send(f"✅ Removed **{role.name}** from {member.mention}.")
            await log_action(bot, "Remove Role", member.name, role.name, ctx.author)
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to remove that role.")
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

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
                    return await ctx.send("❌ This server has reached its emoji limit.", ephemeral=True)

                emoji_bytes = await partial_emoji.read()
                new_emoji = await ctx.guild.create_custom_emoji(
                    name=partial_emoji.name,
                    image=emoji_bytes,
                    reason=f"Stolen by {ctx.author}"
                )
                await ctx.send(f"✅ Successfully stolen {new_emoji} with name `{partial_emoji.name}`.")
                await log_action(bot, "Steal Emoji", new_emoji.name, "Stolen from another server", ctx.author)
                return
            except commands.PartialEmojiConversionFailure:
                if name is None:
                    return await ctx.send(
                        "❌ For URLs, you must provide both the URL and a name.\n"
                        "Usage: `-steal <image_url> <name>` or `/steal url: <image_url> name: <name>`",
                        ephemeral=True
                    )
                image_url = emoji_or_url

                if not image_url.startswith(('http://', 'https://')):
                    return await ctx.send("❌ Please provide a valid HTTP/HTTPS URL.", ephemeral=True)

                if not re.match(r'^https?://.*\.(jpeg|jpg|gif|png)$', image_url, re.IGNORECASE):
                    return await ctx.send("❌ Please provide a valid image URL (jpg, png, or gif)", ephemeral=True)

                if not (2 <= len(name) <= 32):
                    return await ctx.send("❌ Emoji name must be between 2 and 32 characters long.", ephemeral=True)

                if len(ctx.guild.emojis) >= ctx.guild.emoji_limit:
                    return await ctx.send("❌ This server has reached its emoji limit.", ephemeral=True)

                async with aiohttp.ClientSession() as session:
                    async with session.get(image_url) as resp:
                        if resp.status != 200:
                            return await ctx.send(f"❌ Failed to download image (HTTP Status: {resp.status}).", ephemeral=True)
                        if 'image' not in resp.headers.get('Content-Type', ''):
                            return await ctx.send("❌ The provided URL does not point to an image.", ephemeral=True)

                        image_data = await resp.read()
                        if len(image_data) > 256 * 1024:
                            return await ctx.send("❌ Image is too large (maximum 256KB).", ephemeral=True)

                        new_emoji = await ctx.guild.create_custom_emoji(
                            name=name,
                            image=image_data,
                            reason=f"Added by {ctx.author} from URL"
                        )
                        await ctx.send(f"✅ Successfully added {new_emoji} with name `{name}`.")
                        await log_action(bot, "Add Emoji", new_emoji.name, f"Added from URL: {image_url}", ctx.author)

        except discord.HTTPException as e:
            if e.code == 30008:
                await ctx.send("❌ Maximum emoji slots reached for this server.", ephemeral=True)
            elif e.code == 50045:
                await ctx.send("❌ Invalid image format for the emoji.", ephemeral=True)
            else:
                await ctx.send(f"❌ A Discord error occurred: {str(e)}", ephemeral=True)
        except Exception as e:
            await ctx.send(f"❌ An unexpected error occurred: {str(e)}", ephemeral=True)
