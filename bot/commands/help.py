from discord.ext import commands
import discord
from discord.ui import Select, View
import os
from dotenv import load_dotenv

load_dotenv()
BOT_PREFIX = os.getenv("BOT_PREFIX", "-")  # Use "-" if not set in .env

def setup_help(bot):
    bot.remove_command("help")

    @bot.command(name="help")
    async def help_command(ctx):
        embed = discord.Embed(
            title="🤖 **__Bot Help Panel__**",
            description=(
                "**Welcome to the Help Menu!**\n\n"
                "Select a category from the dropdown below to see commands.\n\n"
                f"**👨‍💻 Developer:** `Ayanokouji`"
            ),
            color=discord.Color.blurple()
        )
        embed.set_author(name=bot.user.name, icon_url=bot.user.display_avatar.url)
        embed.set_footer(text="Use the dropdown below to select a command category.")

        select = Select(
            placeholder="🔽️ Choose a category...",
            options=[
                discord.SelectOption(label="Moderation", value="moderation", emoji="🛡️"),
                discord.SelectOption(label="Utility", value="utility", emoji="🛠️"),
                discord.SelectOption(label="AI", value="ai", emoji="🧠"),
            ]
        )

        view = View()
        view.add_item(select)

        async def select_callback(interaction: discord.Interaction):
            value = select.values[0]

            if value == "moderation":
                embed = discord.Embed(
                    title="🛡️ **__Moderation Commands__**",
                    color=discord.Color.red()
                )
                embed.set_author(name=bot.user.name, icon_url=bot.user.display_avatar.url)

                embed.add_field(name="👥 Member Moderation", value=(
                    f"**kick** - Kick a user\n`Usage:` `{BOT_PREFIX}kick @user [reason]`\n"
                    f"**ban** - Ban a user\n`Usage:` `{BOT_PREFIX}ban @user [reason]`\n"
                    f"**unban** - Unban a user\n`Usage:` `{BOT_PREFIX}unban user_id`\n"
                    f"**timeout** - Timeout a user\n`Usage:` `{BOT_PREFIX}timeout @user 10s/m/h`\n"
                    f"**untimeout** - Remove timeout\n`Usage:` `{BOT_PREFIX}untimeout @user`"
                ), inline=False)

                embed.add_field(name="⚠️ Warnings & Logs", value=(
                    f"**warn** - Warn a user\n`Usage:` `{BOT_PREFIX}warn @user [reason]`\n"
                    f"**warnings** - Check user warnings\n`Usage:` `{BOT_PREFIX}warnings @user`\n"
                    f"**clearwarnings** - Clear all warnings\n`Usage:` `{BOT_PREFIX}clearwarnings @user`"
                ), inline=False)

                embed.add_field(name="🧹 Message Management", value=(
                    f"**purge** - Purge messages\n`Usage:` `{BOT_PREFIX}purge 2`\n"
                    f"**snipe** - Show last deleted message\n`Usage:` `{BOT_PREFIX}snipe`"
                ), inline=False)

                embed.add_field(name="🔒 Channel Management", value=(
                    f"**lock** - Lock a channel\n`Usage:` `{BOT_PREFIX}lock #channel`\n"
                    f"**unlock** - Unlock a channel\n`Usage:` `{BOT_PREFIX}unlock #channel`\n"
                    f"**slowmode** - Set slowmode\n`Usage:` `{BOT_PREFIX}slowmode #channel 10s/m/h`\n"
                    f"**hide** - Hide a channel\n`Usage:` `{BOT_PREFIX}hide #channel`\n"
                    f"**unhide** - Unhide a channel\n`Usage:` `{BOT_PREFIX}unhide #channel`\n"
                    f"**nuke** - Nuke a channel\n`Usage:` `{BOT_PREFIX}nuke #channel`"
                ), inline=False)

                embed.add_field(name="🎭 Role Management", value=(
                    f"**addrole** - Add role\n`Usage:` `{BOT_PREFIX}addrole @user @role`\n"
                    f"**removerole** - Remove role\n`Usage:` `{BOT_PREFIX}removerole @user @role`"
                ), inline=False)

                embed.add_field(
                    name="😀 Emoji Management",
                    value=(
                        f"**steal** - Add an emoji\n"
                        f"`Usage:` `{BOT_PREFIX}steal :emoji:` or `{BOT_PREFIX}steal (link) name`"
                    ),
                    inline=False
                )

            elif value == "utility":
                embed = discord.Embed(
                    title="🛠️ **__Utility Commands__**",
                    color=discord.Color.green()
                )
                embed.set_author(name=bot.user.name, icon_url=bot.user.display_avatar.url)

                embed.add_field(name="📊 Bot Info", value=(
                    f"**ping** - Show latency\n`Usage:` `{BOT_PREFIX}ping`\n"
                    f"**uptime** - Show uptime\n`Usage:` `{BOT_PREFIX}uptime`\n"
                    f"**help** - Help menu\n`Usage:` `{BOT_PREFIX}help`"
                ), inline=False)

                embed.add_field(name="🙋 User Info", value=(
                    f"**userinfo** - User info\n`Usage:` `{BOT_PREFIX}userinfo @user`\n"
                    f"**avatar** - Show avatar\n`Usage:` `{BOT_PREFIX}avatar @user`"
                ), inline=False)

                embed.add_field(name="📌 Server Info", value=(
                    f"**serverinfo** - Server info\n`Usage:` `{BOT_PREFIX}serverinfo`\n"
                    f"**roleinfo** - Role info\n`Usage:` `{BOT_PREFIX}roleinfo @role`\n"
                    f"**emojis** - Show emojis\n`Usage:` `{BOT_PREFIX}emojis`\n"
                    f"**boosts** - Server boosts\n`Usage:` `{BOT_PREFIX}boosts`"
                ), inline=False)

                embed.add_field(name="🎉 Fun & Tools", value=(
                    f"**say** - Repeat text\n`Usage:` `{BOT_PREFIX}say Hello`\n"
                    f"**remindme** - Set reminder\n`Usage:` `{BOT_PREFIX}remindme 10m Take a break`\n"
                    f"**invite** - Bot invite\n`Usage:` `{BOT_PREFIX}invite`\n"
                    f"**support** - Support server\n`Usage:` `{BOT_PREFIX}support`\n"
                    f"**suggest** - Suggestion for the developer\n`Usage:` `{BOT_PREFIX}suggest`"
                ), inline=False)

            elif value == "ai":
                embed = discord.Embed(
                    title="🧠 **__AI Commands__**",
                    color=discord.Color.purple()
                )
                embed.set_author(name=bot.user.name, icon_url=bot.user.display_avatar.url)

                embed.add_field(name="🤖 AI Interaction", value=(
                    f"**aichannel** - Set AI channel\n`Usage:` `{BOT_PREFIX}aichannel #channel`\n"
                    f"**ask** - Ask AI\n`Usage:` `{BOT_PREFIX}ask What is AI?`\n"
                    f"**clearhistory** - Clear AI chat\n`Usage:` `{BOT_PREFIX}clearhistory`"
                ), inline=False)

            await interaction.response.edit_message(embed=embed, view=view)

        select.callback = select_callback
        await ctx.send(embed=embed, view=view)
