from discord.ext import commands
import discord
import asyncio
import aiohttp
import typing
from datetime import timedelta

# --- Global Variables and Configuration ---
# These are variables that need to be accessible across different parts of the moderation system.
log_channel = None  # Channel ID where moderation actions will be logged
warnings_db = {}  # A simple in-memory dictionary to store user warnings
last_deleted_message = None  # Stores the last deleted message for the snipe command


# --- Helper Functions ---
# Functions that assist the commands but aren't commands themselves.
async def log_action(bot, action, target, reason, moderator, extra_info=""):
    """
    Logs moderation actions to a predefined log channel.
    
    Parameters
    ----------
    bot: The bot instance to get the channel.
    action: The type of moderation action (e.g., "Kick", "Ban").
    target: The user or entity on whom the action was performed.
    reason: The reason for the action.
    moderator: The user who performed the action.
    extra_info: Any additional information to include in the log.
    """
    if log_channel:
        channel = bot.get_channel(log_channel)
        if channel:
            embed = discord.Embed(
                title=f"Log: {action}",
                description=f"Target: {target}\nReason: {reason or 'None'}\nBy: {moderator}\n{extra_info}",
                color=0x708090  # A greyish color for the embed
            )
            await channel.send(embed=embed)


# --- Core Moderation Commands ---
# These are the main moderation actions like kick, ban, timeout, etc.
def setup_moderation(bot):
    """
    Sets up all moderation commands and event listeners for the bot.
    This function should be called when the bot starts.
    """

    @bot.hybrid_command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick(ctx, member: discord.Member = None, *, reason: str = None):
        """
        Kick a member from the server.
        
        Parameters
        ----------
        member: The member to kick.
        reason: The reason for kicking the member.
        """
        if not member:
            return await ctx.send("Please mention a user to kick.")
        await member.kick(reason=reason)
        await ctx.send(f"Kicked {member.name} for: {reason or 'no reason'}")
        await log_action(bot, "Kick", member.name, reason, ctx.author)

    @bot.hybrid_command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban(ctx, member: discord.Member = None, *, reason: str = None):
        """
        Ban a member from the server.
        
        Parameters
        ----------
        member: The member to ban.
        reason: The reason for banning the member.
        """
        if not member:
            return await ctx.send("Please mention a user to ban.")
        await member.ban(reason=reason)
        await ctx.send(f"Banned {member.name} for: {reason or 'no reason'}")
        await log_action(bot, "Ban", member.name, reason, ctx.author)

    @bot.hybrid_command(name="unban")
    @commands.has_permissions(ban_members=True)
    async def unban(ctx, *, user: str):
        """
        Unban a user from the server.
        
        Parameters
        ----------
        user: The username and discriminator (e.g., "User#1234") of the user to unban.
        """
        banned_users = await ctx.guild.bans()
        
        # Check if the user input contains a discriminator
        if "#" in user:
            name, discriminator = user.split("#")
        else:
            # If no discriminator, try to match by name only (less accurate)
            name = user
            discriminator = None 

        for ban_entry in banned_users:
            if ban_entry.user.name == name and (discriminator is None or ban_entry.user.discriminator == discriminator):
                await ctx.guild.unban(ban_entry.user)
                await ctx.send(f"Unbanned {user}")
                await log_action(bot, "Unban", user, "Manual Unban", ctx.author)
                return
        await ctx.send("User not found in ban list or incorrect format. Please use 'Username#Discriminator' or just 'Username'.")

    @bot.hybrid_command(name="timeout")
    @commands.has_permissions(moderate_members=True)
    async def timeout(ctx, member: discord.Member, duration: str):
        """
        Timeout a member with a specified duration (e.g., 30s, 5m, 1h).
        
        Parameters
        ----------
        member: The member to timeout.
        duration: The duration of the timeout.
        """
        try:
            # Parse the duration string
            seconds = 0
            if duration.endswith('s'):
                seconds = int(duration[:-1])
            elif duration.endswith('m'):
                seconds = int(duration[:-1]) * 60
            elif duration.endswith('h'):
                seconds = int(duration[:-1]) * 3600
            else:
                # Default to seconds if no unit is specified
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
        """
        Remove timeout from a member.
        
        Parameters
        ----------
        member: The member to remove timeout from.
        """
        await member.timeout(None)  # Setting timeout to None removes it
        await ctx.send(f"Removed timeout from {member.name}")
        await log_action(bot, "Untimeout", member.name, "Timeout removed", ctx.author)


# --- Warning System Commands ---
# Commands specifically for managing user warnings.
    @bot.hybrid_command(name="warn")
    @commands.has_permissions(manage_messages=True)
    async def warn(ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """
        Warn a member with a reason.
        
        Parameters
        ----------
        member: The member to warn.
        reason: The reason for the warning.
        """
        if member.id not in warnings_db:
            warnings_db[member.id] = []
        warnings_db[member.id].append(reason)
        await ctx.send(f"Warned {member.name}: {reason}")
        await log_action(bot, "Warn", member.name, reason, ctx.author)

    @bot.hybrid_command(name="warnings")
    async def warnings(ctx, member: discord.Member):
        """
        Check warnings for a member.
        
        Parameters
        ----------
        member: The member to check warnings for.
        """
        warns = warnings_db.get(member.id, [])
        if not warns:
            await ctx.send(f"No warnings for {member.name}.")
        else:
            # Display warnings in a more readable format
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
        """
        Clear all warnings for a member.
        
        Parameters
        ----------
        member: The member to clear warnings for.
        """
        if member.id in warnings_db:
            warnings_db.pop(member.id)
            await ctx.send(f"Cleared all warnings for {member.name}.")
            await log_action(bot, "Clear Warnings", member.name, "All warnings cleared", ctx.author)
        else:
            await ctx.send(f"No warnings found for {member.name} to clear.")


# --- Message Management Commands ---
# Commands related to managing messages in channels.
    @bot.hybrid_command(name="purge")
    @commands.has_permissions(manage_messages=True)
    async def purge(ctx, amount: int):
        """
        Purge (delete) a specified number of messages in the channel.
        
        Parameters
        ----------
        amount: The number of messages to purge (between 1 and 1000).
        """
        if amount <= 0 or amount > 1000:
            return await ctx.send("Amount must be between 1 and 1000.", ephemeral=True)
            
        # Delete amount + 1 because it also deletes the command message
        deleted_messages = await ctx.channel.purge(limit=amount + 1)
        # Send a temporary message confirming the purge
        msg = await ctx.send(f"{len(deleted_messages) - 1} message(s) purged by {ctx.author.mention}.")
        await asyncio.sleep(3)  # Wait for 3 seconds
        await msg.delete()  # Delete the confirmation message

    @bot.hybrid_command(name="snipe")
    async def snipe(ctx):
        """View the most recently deleted message."""
        if last_deleted_message:
            embed = discord.Embed(
                title="Sniped Message",
                description=last_deleted_message.content,
                color=discord.Color.blue()
            )
            embed.set_author(name=last_deleted_message.author.display_name, icon_url=last_deleted_message.author.avatar.url)
            embed.set_footer(text=f"Channel: #{last_deleted_message.channel.name}")
            await ctx.send(embed=embed)
        else:
            await ctx.send("No recently deleted message to snipe.")

    # --- Bot Event Listeners ---
    # Functions that run automatically when certain Discord events happen.
    @bot.event
    async def on_message_delete(message):
        """
        Event listener that saves the last deleted message.
        """
        global last_deleted_message
        last_deleted_message = message


# --- Channel Management Commands ---
# Commands for controlling channel permissions and behavior.
    @bot.hybrid_command(name="lock")
    @commands.has_permissions(manage_channels=True)
    async def lock(ctx):
        """Lock the current channel, preventing @everyone from sending messages."""
        # Overwrite permissions for the default role (which represents @everyone)
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
        await ctx.send("🔒 Channel locked.")

    @bot.hybrid_command(name="unlock")
    @commands.has_permissions(manage_channels=True)
    async def unlock(ctx):
        """Unlock the current channel, allowing @everyone to send messages."""
        # Overwrite permissions for the default role (which represents @everyone)
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
        await ctx.send("🔓 Channel unlocked.")

    @bot.hybrid_command(name="slowmode")
    @commands.has_permissions(manage_channels=True)
    async def slowmode(ctx, seconds: int):
        """
        Set slowmode for the channel (0-21600 seconds).
        
        Parameters
        ----------
        seconds: The delay in seconds for slowmode. Set to 0 to disable.
        """
        if seconds < 0 or seconds > 21600:
            return await ctx.send("Slowmode must be between 0 and 21600 seconds (6 hours).")
        await ctx.channel.edit(slowmode_delay=seconds)
        await ctx.send(f"Set slowmode to {seconds} seconds.")
        await log_action(bot, "Slowmode", ctx.channel.name, f"{seconds} seconds", ctx.author)

    @bot.hybrid_command(name="hide")
    @commands.has_permissions(manage_channels=True)
    async def hide(ctx):
        """Hide the current channel from @everyone."""
        # Prevent the default role from viewing the channel
        await ctx.channel.set_permissions(ctx.guild.default_role, view_channel=False)
        await ctx.send("Channel hidden.")
        await log_action(bot, "Hide Channel", ctx.channel.name, "Hidden from @everyone", ctx.author)

    @bot.hybrid_command(name="unhide")
    @commands.has_permissions(manage_channels=True)
    async def unhide(ctx):
        """Unhide the current channel, making it visible to @everyone."""
        # Allow the default role to view the channel
        await ctx.channel.set_permissions(ctx.guild.default_role, view_channel=True)
        await ctx.send("Channel visible.")
        await log_action(bot, "Unhide Channel", ctx.channel.name, "Visible to @everyone", ctx.author)

    @bot.hybrid_command(name="nuke")
    @commands.has_permissions(manage_channels=True)
    async def nuke(ctx):
        """
        Nuke (clone and delete) the current channel, effectively clearing all messages.
        Requires user confirmation.
        """
        # A simple prompt for confirmation (assuming ctx.prompt exists or you implement it)
        # If ctx.prompt is not available, you would need to implement a reaction-based confirmation.
        try:
            confirm = await ctx.send("Are you sure you want to nuke this channel? React with ✅ to confirm.")
            await confirm.add_reaction("✅")

            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) == '✅' and reaction.message.id == confirm.id

            await bot.wait_for('reaction_add', check=check, timeout=30.0) # Wait for reaction for 30 seconds
            
            new_channel = await ctx.channel.clone() # Create a copy of the channel
            await ctx.channel.delete() # Delete the original channel
            await new_channel.send("💥 Channel nuked!")
            await log_action(bot, "Channel Nuke", new_channel.name, "Channel recreated", ctx.author)

        except asyncio.TimeoutError:
            await ctx.send("Nuke cancelled. You did not confirm in time.")
        except Exception as e:
            await ctx.send(f"An error occurred during nuke: {e}")


# --- Role Management Commands ---
# Commands for adding and removing roles.
    @bot.hybrid_command(name="addrole")
    @commands.has_permissions(manage_roles=True)
    async def addrole(ctx, member: discord.Member, role: discord.Role):
        """
        Add a role to a member.
        
        Parameters
        ----------
        member: The member to add the role to.
        role: The role to add.
        """
        try:
            await member.add_roles(role)
            await ctx.send(f"✅ Added **{role.name}** to {member.mention}.")
            await log_action(bot, "Add Role", member.name, role.name, ctx.author)
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to add that role. Make sure my role is above the role you're trying to add.")
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

    @bot.hybrid_command(name="removerole")
    @commands.has_permissions(manage_roles=True)
    async def removerole(ctx, member: discord.Member, role: discord.Role):
        """
        Remove a role from a member.
        
        Parameters
        ----------
        member: The member to remove the role from.
        role: The role to remove.
        """
        try:
            await member.remove_roles(role)
            await ctx.send(f"✅ Removed **{role.name}** from {member.mention}.")
            await log_action(bot, "Remove Role", member.name, role.name, ctx.author)
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to remove that role. Make sure my role is above the role you're trying to remove.")
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")


# --- Emoji Management Commands ---
# Commands for managing server emojis.
    @bot.hybrid_command(name="steal")
    @commands.has_permissions(manage_emojis=True)
    async def steal(ctx, emoji: typing.Optional[discord.PartialEmoji] = None, image_url: typing.Optional[str] = None, name: typing.Optional[str] = None):
        """
        Steal an emoji from another server or add one from a URL.
        
        Usage:
        - `steal :emoji:` (steals with original name)
        - `steal <image_url> <name>` (adds emoji from URL with given name)
        
        Parameters
        ----------
        emoji: An existing emoji to steal.
        image_url: A URL to an image to create an emoji from.
        name: The desired name for the new emoji when using a URL.
        """
        try:
            if emoji:
                # Steal emoji case
                emoji_bytes = await emoji.read()
                new_emoji = await ctx.guild.create_custom_emoji(name=emoji.name, image=emoji_bytes)
                await ctx.send(f"✅ Successfully stolen {new_emoji} with name `{emoji.name}`.")
                await log_action(bot, "Steal Emoji", new_emoji.name, "Stolen from another server", ctx.author)
            elif image_url and name:
                # URL case - improved URL validation
                if not image_url.startswith(('http://', 'https://')):
                    return await ctx.send("❌ Please provide a valid HTTP/HTTPS URL.", ephemeral=True)
                
                if not (2 <= len(name) <= 32):
                    return await ctx.send("❌ Emoji name must be between 2 and 32 characters long.", ephemeral=True)
                
                # Download the image
                async with aiohttp.ClientSession() as session:
                    try:
                        async with session.get(image_url) as resp:
                            if resp.status != 200:
                                return await ctx.send(f"❌ Failed to download image (HTTP Status: {resp.status}).", ephemeral=True)
                            
                            # Check content type
                            content_type = resp.headers.get('Content-Type', '')
                            if 'image' not in content_type:
                                return await ctx.send("❌ The provided URL does not point to an image.", ephemeral=True)
                            
                            image_data = await resp.read()
                            
                            # Check file size (Discord limit is 256KB)
                            if len(image_data) > 256 * 1024:
                                return await ctx.send("❌ Image is too large (maximum 256KB).", ephemeral=True)
                            
                            # Create the emoji
                            new_emoji = await ctx.guild.create_custom_emoji(name=name, image=image_data)
                            await ctx.send(f"✅ Successfully added {new_emoji} with name `{name}`.")
                            await log_action(bot, "Add Emoji", new_emoji.name, f"Added from URL: {image_url}", ctx.author)
                    except aiohttp.InvalidURL:
                        await ctx.send("❌ Invalid URL provided.", ephemeral=True)
                    except Exception as e:
                        await ctx.send(f"❌ Error downloading image: {str(e)}", ephemeral=True)
            else:
                await ctx.send("❌ Invalid usage. Use `steal :emoji:` or `steal <image_url> <name>`.", ephemeral=True)
                
        except discord.HTTPException as e:
            if e.code == 30008:
                await ctx.send("❌ Maximum emoji slots reached for this server (50 for normal servers, 250 for boosted).", ephemeral=True)
            elif e.code == 50045:
                await ctx.send("❌ Invalid image format for the emoji.", ephemeral=True)
            else:
                await ctx.send(f"❌ A Discord error occurred: {str(e)}", ephemeral=True)
        except Exception as e:
            await c