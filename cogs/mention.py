"""
Mention Reply Cog — Responds when someone mentions the bot directly.
Components V2 container style for RynoX bot.
"""

import discord
import os
from discord.ext import commands
from discord import ui


# ── Config ────────────────────────────────────────────────────────────────────

BOT_NAME = "RynoX"
DEFAULT_ACCENT = discord.Colour(0xFFFFFF)

# Links — change these to your real URLs
INVITE_LINK = os.getenv("INVITE_URL", "https://discord.com/oauth2/authorize?client_id=1565750430477058098&permissions=8&integration_type=0&scope=bot+applications.commands")
SUPPORT_LINK = os.getenv("SUPPORT_SERVER", "https://discord.gg/TKDHTJ85Ta")

FOOTER_TEXT = f"Powered by {BOT_NAME}™ Development"


# ── Cog ───────────────────────────────────────────────────────────────────────

class MentionReply(commands.Cog):
    """Responds with bot info when mentioned directly."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        # Check if bot was mentioned directly (just the mention, nothing else)
        stripped = message.content.strip()
        if stripped not in (f"<@{self.bot.user.id}>", f"<@!{self.bot.user.id}>"):
            return

        # Get prefix for this guild
        try:
            prefix = await self.bot.get_prefix(message)
            if isinstance(prefix, (list, tuple)):
                prefix = [p for p in prefix if not p.startswith("<@")]
                prefix = prefix[0] if prefix else "."
        except Exception:
            prefix = "."

        # ── Build CV2 container (matches screenshot exactly) ─────────────────
        view = ui.LayoutView(timeout=None)
        c = ui.Container(accent_color=DEFAULT_ACCENT)

        # Title (large)
        c.add_item(ui.TextDisplay(f"## Hey, I'm {BOT_NAME}"))

        # Separator line under title (visible)
        c.add_item(ui.Separator(visible=True))

        # Body text — exactly like screenshot
        body_text = (
            f"**Server Prefix:** `{prefix}`\n"
            f"**Get Started:** Run `{prefix}help` to discover all features\n"
            f"**Support:** Having issues ? Join our [Support Server]({SUPPORT_LINK})"
        )
        c.add_item(ui.TextDisplay(body_text))

        # Buttons row
        c.add_item(ui.ActionRow(
            ui.Button(
                label="Invite Me",
                style=discord.ButtonStyle.link,
                url=INVITE_LINK,
            ),
            ui.Button(
                label="Support Server",
                style=discord.ButtonStyle.link,
                url=SUPPORT_LINK,
            ),
        ))

        # Separator line above footer (visible)
        c.add_item(ui.Separator(visible=True))

        # Footer
        c.add_item(ui.TextDisplay(f"-# {FOOTER_TEXT}"))

        view.add_item(c)

        try:
            await message.channel.send(view=view)
        except discord.Forbidden:
            pass
        except Exception as e:
            print(f"[MentionReply] Error: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(MentionReply(bot))