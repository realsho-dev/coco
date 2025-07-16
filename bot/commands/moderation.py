from discord.ext import commands
import discord
import asyncio
from datetime import timedelta

log_channel = None
warnings_db = {}
last_deleted_message = None


def setup_moderation(bot):
    async def log_action(action, target, reason, moderator, extra_info=""):
        if log_channel:
            channel = bot.get_channel(log_channel)
            if channel:
                embed = discord.Embed(
                    title=f"Log: {action}",
                    description=f"Target: {target}\nReason: {reason or 'None'}\nBy: {moderator}\n{extra_info}",
                    color=0x708090
                )
                await channel.send(embed=embed)

    @bot.hybrid_command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick(ctx, member: discord.Member = None, *, reason: str = None):
        """Kick a member from the server"""
        if not member:
            return await ctx.send("Please mention a user to kick.")
        await member.kick(reason=reason)
        await ctx.send(f"Kicked {member.name} for: {reason}")
        await log_action("Kick", member.name, reason, ctx.author)

    @bot.hybrid_command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban(ctx, member: discord.Member = None, *, reason: str = None):
        """Ban a member from the server"""
        if not member:
            return await ctx.send("Please mention a user to ban.")
        await member.ban(reason=reason)
        await ctx.send(f"Banned {member.name} for: {reason}")
        await log_action("Ban", member.name, reason, ctx.author)

    @bot.hybrid_command(name="unban")
    @commands.has_permissions(ban_members=True)
    async def unban(ctx, *, user):
        """Unban a user from the server"""
        banned_users = await ctx.guild.bans()
        name, discriminator = user.split("#")
        for ban_entry in banned_users:
            if ban_entry.user.name == name and ban_entry.user.discriminator == discriminator:
                await ctx.guild.unban(ban_entry.user)
                await ctx.send(f"Unbanned {user}")
                return
        await ctx.send("User not found in ban list.")

    @bot.hybrid_command(name="timeout")
    @commands.has_permissions(moderate_members=True)
    async def timeout(ctx, member: discord.Member, duration: str):
        """
        Timeout a member with duration (e.g., 30s, 5m, 1h)
        
        Parameters
        ----------
        member: The member to timeout
        duration: Duration of timeout (e.g., 30s, 5m, 1h)
        """
        try:
            # Parse duration
            if duration.endswith('s'):
                seconds = int(duration[:-1])
            elif duration.endswith('m'):
                seconds = int(duration[:-1]) * 60
            elif duration.endswith('h'):
                seconds = int(duration[:-1]) * 3600
            else:
                seconds = int(duration)  # Default to seconds if no unit specified
                
            await member.timeout(discord.utils.utcnow() + timedelta(seconds=seconds))
            await ctx.send(f"Timed out {member.name} for {duration}")
            await log_action("Timeout", member.name, duration, ctx.author)
        except ValueError:
            await ctx.send("Invalid duration format. Use format like 30s, 5m, 1h")

    @bot.hybrid_command(name="untimeout")
    @commands.has_permissions(moderate_members=True)
    async def untimeout(ctx, member: discord.Member):
        """Remove timeout from a member"""
        await member.timeout(None)
        await ctx.send(f"Removed timeout from {member.name}")
        await log_action("Untimeout", member.name, None, ctx.author)

    @bot.hybrid_command(name="warn")
    @commands.has_permissions(manage_messages=True)
    async def warn(ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Warn a member with a reason"""
        if member.id not in warnings_db:
            warnings_db[member.id] = []
        warnings_db[member.id].append(reason)
        await ctx.send(f"Warned {member.name}: {reason}")
        await log_action("Warn", member.name, reason, ctx.author)

    @bot.hybrid_command(name="warnings")
    async def warnings(ctx, member: discord.Member):
        """Check warnings for a member"""
        warns = warnings_db.get(member.id, [])
        if not warns:
            await ctx.send(f"No warnings for {member.name}")
        else:
            await ctx.send(f"Warnings for {member.name}: {', '.join(warns)}")

    @bot.hybrid_command(name="clearwarnings")
    @commands.has_permissions(manage_messages=True)
    async def clearwarnings(ctx, member: discord.Member):
        """Clear all warnings for a member"""
        warnings_db.pop(member.id, None)
        await ctx.send(f"Cleared warnings for {member.name}")
        await log_action("Clear Warnings", member.name, None, ctx.author)

    @bot.hybrid_command(name="purge")
    @commands.has_permissions(manage_messages=True)
    async def purge(ctx, amount: int):
        """Purge messages in the channel"""
        if amount <= 0 or amount > 1000:
            return await ctx.send("Amount must be between 1 and 1000", ephemeral=True)
            
        deleted_messages = await ctx.channel.purge(limit=amount + 1)
        msg = await ctx.send(f"{len(deleted_messages) - 1} message(s) purged by {ctx.author.mention}")
        await asyncio.sleep(3)
        await msg.delete()

    @bot.hybrid_command(name="snipe")
    async def snipe(ctx):
        """View the most recently deleted message"""
        if last_deleted_message:
            await ctx.send(f"Sniped message from {last_deleted_message.author}: {last_deleted_message.content}")
        else:
            await ctx.send("No recently deleted message.")

    @bot.event
    async def on_message_delete(message):
        global last_deleted_message
        last_deleted_message = message

    @bot.hybrid_command(name="lock")
    @commands.has_permissions(manage_channels=True)
    async def lock(ctx):
        """Lock the current channel"""
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
        await ctx.send("🔒 Channel locked")

    @bot.hybrid_command(name="unlock")
    @commands.has_permissions(manage_channels=True)
    async def unlock(ctx):
        """Unlock the current channel"""
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
        await ctx.send("🔓 Channel unlocked")

    @bot.hybrid_command(name="slowmode")
    @commands.has_permissions(manage_channels=True)
    async def slowmode(ctx, seconds: int):
        """Set slowmode for the channel"""
        if seconds < 0 or seconds > 21600:
            return await ctx.send("Slowmode must be between 0 and 21600 seconds (6 hours)")
        await ctx.channel.edit(slowmode_delay=seconds)
        await ctx.send(f"Set slowmode to {seconds} seconds")

    @bot.hybrid_command(name="hide")
    @commands.has_permissions(manage_channels=True)
    async def hide(ctx):
        """Hide the current channel"""
        await ctx.channel.set_permissions(ctx.guild.default_role, view_channel=False)
        await ctx.send("Channel hidden")

    @bot.hybrid_command(name="unhide")
    @commands.has_permissions(manage_channels=True)
    async def unhide(ctx):
        """Unhide the current channel"""
        await ctx.channel.set_permissions(ctx.guild.default_role, view_channel=True)
        await ctx.send("Channel visible")

    @bot.hybrid_command(name="nuke")
    @commands.has_permissions(manage_channels=True)
    async def nuke(ctx):
        """Nuke (clone and delete) the current channel"""
        confirm = await ctx.prompt("Are you sure you want to nuke this channel?")
        if not confirm:
            return await ctx.send("Nuke cancelled")
            
        new_channel = await ctx.channel.clone()
        await ctx.channel.delete()
        await new_channel.send("💥 Channel nuked")

    @bot.hybrid_command(name="addrole")
    @commands.has_permissions(manage_roles=True)
    async def addrole(ctx, member: discord.Member, role: discord.Role):
        """Add a role to a member"""
        try:
            await member.add_roles(role)
            await ctx.send(f"✅ Added {role.name} to {member.mention}")
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to add that role.")
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

    @bot.hybrid_command(name="removerole")
    @commands.has_permissions(manage_roles=True)
    async def removerole(ctx, member: discord.Member, role: discord.Role):
        """Remove a role from a member"""
        try:
            await member.remove_roles(role)
            await ctx.send(f"✅ Removed {role.name} to {member.mention}")
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to remove that role.")
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

    @bot.hybrid_command(name="steal")
    @commands.has_permissions(manage_emojis=True)
    async def steal(ctx, emoji: discord.PartialEmoji = None, name: str = None, image_url: str = None):
        """
        Steal an emoji from another server or add from URL
        
        Usage:
        -steal :emoji: (steals with original name)
        -steal :image_url: name (adds emoji from URL with given name)
        """
        if not emoji and not image_url:
            return await ctx.send("You must provide either an emoji or an image URL")
            
        try:
            if emoji:
                # Steal emoji with original name
                emoji_bytes = await emoji.read()
                new_emoji = await ctx.guild.create_custom_emoji(name=emoji.name, image=emoji_bytes)
                await ctx.send(f"Stolen emoji {new_emoji} with name `{emoji.name}`")
            else:
                # Add from URL with custom name
                if not name:
                    return await ctx.send("You must provide a name when adding from URL")
                    
                async with bot.session.get(image_url) as resp:
                    if resp.status != 200:
                        return await ctx.send("Could not download the image from the URL")
                    image_data = await resp.read()
                    
                new_emoji = await ctx.guild.create_custom_emoji(name=name, image=image_data)
                await ctx.send(f"Added emoji {new_emoji} with name `{name}`")
        except discord.HTTPException as e:
            if e.code == 30008:
                await ctx.send("Maximum number of emojis reached (50 for normal servers, 250 for boosted)")
            else:
                await ctx.send(f"Error: {str(e)}")
        except Exception as e:
            await ctx.send(f"Error: {str(e)}")

    @bot.hybrid_command(name="deleteemoji")
    @commands.has_permissions(manage_emojis=True)
    async def deleteemoji(ctx, emoji: discord.Emoji):
        """Delete an emoji from the server"""
        await emoji.delete()
        await ctx.send(f"Deleted emoji {emoji.name}")

    @bot.event
    async def on_command_error(ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(f"You don't have permission to use this command. Required permissions: {', '.join(error.missing_permissions)}")
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send(f"I don't have permission to perform this action. Required permissions: {', '.join(error.missing_permissions)}")
        elif isinstance(error, commands.CommandInvokeError):
            await ctx.send(f"An error occurred while executing the command: {str(error.original)}")