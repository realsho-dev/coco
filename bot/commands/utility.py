from discord.ext import commands
import discord
import time
import asyncio
from datetime import datetime, timedelta
import re
import aiohttp

start_time = time.time()

def setup_utility(bot):
    @bot.hybrid_command(name="ping")
    async def ping(ctx):
        """Check the bot's latency"""
        try:
            await ctx.send(f"🏓 **Pong!** Latency is `{round(bot.latency * 1000)}ms`.")
        except Exception as e:
            await ctx.send(f"⚠️ **Error:** Cannot check latency now.\nError: {e}")

    @bot.hybrid_command(name="uptime")
    async def uptime(ctx):
        """Shows the bot's uptime"""
        try:
            seconds = int(time.time() - start_time)
            days, seconds = divmod(seconds, 86400)
            hours, seconds = divmod(seconds, 3600)
            minutes, seconds = divmod(seconds, 60)
            await ctx.send(
                f"⏰ **Uptime:** {days} days, {hours} hours, {minutes} minutes, {seconds} seconds.\n"
                f"**Bot started:** <t:{int(start_time)}:R>"
            )
        except Exception as e:
            await ctx.send(f"⚠️ **Error:** Cannot get uptime now.\nError: {e}")

    @bot.hybrid_command(name="help")
    async def help(ctx):
        """Shows help information"""
        try:
            embed = discord.Embed(title="ℹ️ Bot Help", color=0x5865F2)
            embed.add_field(
                name="Utility Commands",
                value="`ping`, `uptime`, `userinfo`, `avatar`, `serverinfo`, `roleinfo`, `emojis`, `boosts`, `remindme`, `invite`, `support`, `suggest`, `say`",
                inline=False
            )
            embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"⚠️ **Error:** Cannot show help now.\nError: {e}")

    @bot.hybrid_command(name="userinfo")
    async def userinfo(ctx, member: discord.Member = None):
        """Get detailed information about a user"""
        try:
            member = member or ctx.author
            roles = [role.mention for role in member.roles if role != ctx.guild.default_role]
            
            embed = discord.Embed(color=member.color, timestamp=datetime.utcnow())
            embed.set_author(name=f"{member}", icon_url=member.display_avatar.url)
            embed.set_thumbnail(url=member.display_avatar.url)
            
            embed.add_field(name="🆔 ID", value=f"`{member.id}`", inline=True)
            embed.add_field(name="📛 Nickname", value=f"`{member.nick or 'None'}`", inline=True)
            embed.add_field(name="🔰 Account Created", value=f"<t:{int(member.created_at.timestamp())}:R>", inline=True)
            embed.add_field(name="📥 Joined Server", value=f"<t:{int(member.joined_at.timestamp())}:R>", inline=True)
            embed.add_field(name="💎 Booster", value=f"{'✅' if member.premium_since else '❌'}", inline=True)
            embed.add_field(name="🤖 Bot", value=f"{'✅' if member.bot else '❌'}", inline=True)
            
            if roles:
                embed.add_field(
                    name=f"🎭 Roles ({len(roles)})",
                    value=" ".join(roles[:10]) + (f" +{len(roles)-10} more..." if len(roles) > 10 else ""),
                    inline=False
                )
            
            embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send("⚠️ **Error:** Could not get user info. Error: {}".format(e))

    @bot.hybrid_command(name="avatar")
    async def avatar(ctx, member: discord.Member = None):
        """Shows user's avatar"""
        try:
            member = member or ctx.author
            avatar_url = member.display_avatar.url

            embed = discord.Embed(
                title=f"🖼️ Avatar - {member}",
                color=0x5865F2,
                timestamp=datetime.utcnow()
            )
            embed.set_image(url=avatar_url)
            embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send("⚠️ **Error:** Could not display avatar. Error: {}".format(e))

    @bot.hybrid_command(name="serverinfo")
    async def serverinfo(ctx):
        """Get detailed information about this server"""
        try:
            guild = ctx.guild
            embed = discord.Embed(
                title=f"ℹ️ Server Info: {guild.name}",
                color=0x5865F2,
                timestamp=datetime.utcnow()
            )
            if guild.icon:
                embed.set_thumbnail(url=guild.icon.url)
            embed.add_field(name="👑 Owner", value=f"{guild.owner.mention}\n`{guild.owner_id}`", inline=True)
            embed.add_field(name="🆔 Server ID", value=f"`{guild.id}`", inline=True)
            embed.add_field(name="📅 Created", value=f"<t:{int(guild.created_at.timestamp())}:R>", inline=True)
            
            embed.add_field(name="👥 Members", value=f"Total: {guild.member_count}\nHumans: {sum(not m.bot for m in guild.members)}\nBots: {sum(m.bot for m in guild.members)}", inline=True)
            embed.add_field(name="💎 Boosts", value=f"Level {guild.premium_tier}\n{guild.premium_subscription_count} boosts", inline=True)
            embed.add_field(name="📊 Channels", value=f"Text: {len(guild.text_channels)}\nVoice: {len(guild.voice_channels)}\nCategories: {len(guild.categories)}", inline=True)
            embed.add_field(name="🔐 Verification", value=str(guild.verification_level).title(), inline=True)
            embed.add_field(name="😀 Emojis", value=f"{len(guild.emojis)}/{guild.emoji_limit}", inline=True)
            embed.add_field(name="🎨 Features", value=", ".join([f"`{f}`" for f in guild.features]) or "None", inline=False)
            if guild.banner:
                embed.set_image(url=guild.banner.url)
            embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send("⚠️ **Error:** Could not get server info. Error: {}".format(e))

    @bot.hybrid_command(name="roleinfo")
    async def roleinfo(ctx, role: discord.Role):
        """Get information about a role"""
        try:
            embed = discord.Embed(
                title=f"🎭 Role Info: {role.name}",
                color=role.color,
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="🆔 ID", value=f"`{role.id}`", inline=True)
            embed.add_field(name="🎨 Color", value=f"`{str(role.color)}`", inline=True)
            embed.add_field(name="👥 Members", value=f"`{len(role.members)}`", inline=True)
            embed.add_field(name="📅 Created", value=f"<t:{int(role.created_at.timestamp())}:R>", inline=True)
            embed.add_field(name="💪 Hoisted", value=f"{'✅' if role.hoist else '❌'}", inline=True)
            embed.add_field(name="💬 Mentionable", value=f"{'✅' if role.mentionable else '❌'}", inline=True)
            
            perms = []
            for perm, value in role.permissions:
                if value:
                    perms.append(f"`{perm}`")
            perm_display = " ".join(perms[:10]) + (f" +{len(perms)-10} more..." if len(perms) > 10 else "") if perms else "None"
            embed.add_field(name="🔑 Permissions", value=perm_display, inline=False)
            embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send("⚠️ **Error:** Could not get role info. Error: {}".format(e))

    @bot.hybrid_command(name="emojis")
    async def emojis(ctx):
        """List all server emojis"""
        try:
            if not ctx.guild.emojis:
                return await ctx.send("😀 **Info:** This server has no custom emojis.")
            emojis = [str(e) for e in ctx.guild.emojis]
            chunks = [emojis[i:i + 20] for i in range(0, len(emojis), 20)]
            for chunk in chunks:
                embed = discord.Embed(
                    title=f"😀 Emojis ({len(ctx.guild.emojis)})",
                    description=" ".join(chunk),
                    color=0x5865F2
                )
                await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send("⚠️ **Error:** Cannot show emojis. Error: {}".format(e))

    @bot.hybrid_command(name="boosts")
    async def boosts(ctx):
        """Show server boost information"""
        try:
            guild = ctx.guild
            embed = discord.Embed(
                title=f"💎 {guild.name} Boost Status",
                color=0xFF73FA,
                description=f"Level {guild.premium_tier} • {guild.premium_subscription_count} boosts"
            )
            if guild.premium_subscription_count >= 2:
                next_level = guild.premium_tier + 1
                if next_level <= 3:
                    needed = {1: 2, 2: 15, 3: 30}[next_level] - guild.premium_subscription_count
                    embed.add_field(name="Next Level", value=f"Need {needed} more boost{'s' if needed != 1 else ''} for level {next_level}")
            if hasattr(guild, "premium_subscribers") and guild.premium_subscribers:
                boost_list = "\n".join(m.mention for m in guild.premium_subscribers[:10])
                if len(guild.premium_subscribers) > 10:
                    boost_list += f"\n+{len(guild.premium_subscribers)-10} more"
                embed.add_field(name="Boosters", value=boost_list, inline=False)
            if guild.banner:
                embed.set_image(url=guild.banner.url)
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send("⚠️ **Error:** Cannot show boost info. Error: {}".format(e))

    @bot.hybrid_command(name="remindme")
    async def remindme(ctx, time_str: str, *, reminder):
        """Set a reminder (e.g., '30m do homework')"""
        try:
            match = re.match(r"(\d+)([smhd])", time_str)
            if not match:
                return await ctx.send("❌ **Error:** Invalid format! Use for example `10m`, `1h`, or `2d`.")
            num, unit = int(match.group(1)), match.group(2)
            seconds = num * {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}[unit]
            if seconds > 2592000:
                return await ctx.send("❌ **Error:** Maximum reminder is 30 days (2,592,000 seconds).")
            time_names = {'s': 'second', 'm': 'minute', 'h': 'hour', 'd': 'day'}
            human_time = f"{num} {time_names[unit]}{'s' if num != 1 else ''}"
            embed = discord.Embed(
                title="⏰ Reminder Set!",
                description=f"I will remind you in **{human_time}** about:\n\n> {reminder}",
                color=0x5865F2
            )
            embed.set_footer(text=f"Reminder set by {ctx.author}", icon_url=ctx.author.display_avatar.url)
            await ctx.send(embed=embed)
            await asyncio.sleep(seconds)
            await ctx.send(f"{ctx.author.mention} ⏰ **Reminder:** {reminder}")
        except Exception as e:
            await ctx.send(f"⚠️ **Error:** Could not set reminder. Error: {e}")

    @bot.hybrid_command(name="invite")
    async def invite(ctx):
        """Get the bot's invite link"""
        try:
            perms = discord.Permissions(
                manage_roles=True,
                kick_members=True,
                ban_members=True,
                manage_channels=True,
                view_audit_log=True,
                moderate_members=True,
                manage_messages=True
            )
            link = discord.utils.oauth_url(bot.user.id, permissions=perms)
            embed = discord.Embed(
                title="🤖 Invite Me To Your Server",
                description=f"[**Click here to invite me!**]({link})",
                color=0x5865F2
            )
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send("⚠️ **Error:** Could not fetch invite link. Error: {}".format(e))

    @bot.hybrid_command(name="support")
    async def support(ctx):
        """Get support server invite"""
        try:
            embed = discord.Embed(
                title="🛠️ Need Support?",
                description="Join our support server: [**Click Here**](https://discord.gg/your-support-link)",
                color=0x5865F2
            )
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send("⚠️ **Error:** Could not show support link. Error: {}".format(e))

    @bot.hybrid_command(name="suggest")
    async def suggest(ctx, *, suggestion):
        """Send a suggestion to the suggestion channel"""
        SUGGESTION_CHANNEL_ID = 1393148853095764009  # <-- Change to your suggestion channel ID
        try:
            channel = bot.get_channel(SUGGESTION_CHANNEL_ID)
            if not channel:
                return await ctx.send("❌ **Error:** Suggestion channel not found. Please contact the staff!")
            embed = discord.Embed(
                title="💡 New Suggestion",
                description=suggestion,
                color=discord.Color.orange(),
                timestamp=datetime.utcnow()
            )
            embed.set_footer(text=f"From {ctx.author}", icon_url=ctx.author.display_avatar.url)
            await channel.send(embed=embed)
            await ctx.send("✅ **Success:** Your suggestion has been sent!")
        except Exception as e:
            await ctx.send(f"⚠️ **Error:** Could not send suggestion. Error: {e}")

    @bot.hybrid_command(name="say")
    @commands.has_permissions(manage_messages=True)
    async def say(ctx, *, message: str):
        """Make the bot say something (no mass mentions allowed)"""
        banned_phrases = ["@everyone", "@here"]
        if any(phrase in message for phrase in banned_phrases):
            return await ctx.send("❌ **Error:** I cannot say messages that mention everyone or here.")
        # Prevent any mentions of roles by <@&ID>
        message = re.sub(r"<@&\d+>", "[Role Mention Blocked]", message)
        try:
            await ctx.message.delete()
        except Exception:
            pass  # No error if cannot delete
        try:
            await ctx.send(message)
        except Exception as e:
            await ctx.send(f"⚠️ **Error:** Could not send message. Error: {e}")

# Basic error handler for permission and argument problems
@commands.Cog.listener()
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ **Error:** You do not have permission to use this command.")
    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.send("❌ **Error:** I do not have permission to do this action. Please check my permissions.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ **Error:** Missing input. Usage: `{ctx.prefix}{ctx.command} {ctx.command.signature}`")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ **Error:** Wrong input. Please check your values.")
    else:
        await ctx.send(f"⚠️ **Error:** {str(error)}")

# Add to your bot. Example:
# bot = commands.Bot(...)
# setup_utility(bot)
