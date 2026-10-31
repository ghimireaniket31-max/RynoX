"""
cogs/webhook_logger.py
═══════════════════════════════════════════════════════════════
RynoX — Global Webhook Logging System
═══════════════════════════════════════════════════════════════
Logs to dedicated webhooks:
  • Every command used (who, where, what)
  • Guild joins (new server stats)
  • Guild leaves (departing server stats)
  • Command errors (full trace)
  • Bot ready event

Component V2 container style + separators
═══════════════════════════════════════════════════════════════
"""

import discord
from discord.ext import commands
from discord import ui
import aiohttp
import asyncio
import traceback
import os
from datetime import datetime, timezone


# ═══════════════════════════════════════════════════════════════
#  😀  EMOJIS (Top — replace IDs here only)
# ═══════════════════════════════════════════════════════════════

from NIXO_STUDIO.emojis import E as _EMGR
import re as _re

# Local key -> central emojis.json key (sourced from NIXO_STUDIO/emojis.py)
_LOCAL_KEY_MAP = {
    "success": "SUCCESS",
    "error": "ERROR",
    "info": "INFO",
    "dot": "DOT",
    "join": "JOIN",
    "leave": "LEAVE",
    "command": "COMMAND",
    "user": "USER",
    "server": "SERVER",
    "channel": "CHANNEL",
    "crown": "CROWN",
    "boost": "BOOST",
    "members": "MEMBERS",
    "bots": "BOTS",
    "clock": "CLOCK",
    "online": "ONLINE",
    "warning": "WARNING",
    "trace": "TRACE",
}

def E(key: str) -> discord.PartialEmoji:
    """Returns a discord.PartialEmoji for buttons/select options."""
    s = _EMGR[_LOCAL_KEY_MAP.get(key, key.upper())]
    m = _re.match(r'<(a)?:([A-Za-z0-9_]+):(\d+)>', s)
    if m:
        return discord.PartialEmoji(name=m.group(2), id=int(m.group(3)), animated=bool(m.group(1)))
    return discord.PartialEmoji(name='grey_arrw', id=1517367908714549308)

def ES(key: str) -> str:
    """Returns the raw emoji string for text/embeds."""
    return _EMGR[_LOCAL_KEY_MAP.get(key, key.upper())]


# ═══════════════════════════════════════════════════════════════
#  🎨  CONFIG — paste your webhook URLs here OR set in .env
# ═══════════════════════════════════════════════════════════════

# Read from .env (preferred) — fallback to empty
WEBHOOK_COMMANDS    = os.getenv("WEBHOOK_COMMANDS",    "")   # all command uses
WEBHOOK_GUILD_JOIN  = os.getenv("WEBHOOK_GUILD_JOIN",  "")   # guild join logs
WEBHOOK_GUILD_LEAVE = os.getenv("WEBHOOK_GUILD_LEAVE", "")   # guild leave logs
WEBHOOK_ERRORS      = os.getenv("WEBHOOK_ERRORS",      "")   # command errors
WEBHOOK_READY       = os.getenv("WEBHOOK_READY",       "")   # bot startup

ACCENT_COLOR = discord.Colour(0xFFFFFF)   # pure white
BOT_NAME     = "RynoX"


# ═══════════════════════════════════════════════════════════════
#  🛠️  HELPERS
# ═══════════════════════════════════════════════════════════════

def _utcnow_ts() -> int:
    return int(datetime.now(timezone.utc).timestamp())


def _truncate(text: str, limit: int = 1000) -> str:
    if len(text) <= limit:
        return text
    return text[:limit - 3] + "..."


def _make_container(*items) -> ui.Container:
    return ui.Container(*items, accent_color=ACCENT_COLOR)


# ═══════════════════════════════════════════════════════════════
#  📦  CV2 LAYOUT BUILDERS
# ═══════════════════════════════════════════════════════════════

def _command_log_view(
    bot: commands.Bot,
    ctx: commands.Context,
) -> ui.LayoutView:
    """Log container for a command usage."""
    view = ui.LayoutView(timeout=None)

    user    = ctx.author
    guild   = ctx.guild
    channel = ctx.channel
    cmd     = ctx.command

    # Header (with user avatar)
    header_text = ui.TextDisplay(
        f"## {ES('command')} Command Used\n"
        f"-# `{cmd.qualified_name if cmd else 'Unknown'}`"
    )

    try:
        section = ui.Section(
            header_text,
            accessory=ui.Thumbnail(
                media=discord.UnfurledMediaItem(url=user.display_avatar.url),
                description=str(user),
            ),
        )
        container_items = [section, ui.Separator()]
    except Exception:
        container_items = [header_text, ui.Separator()]

    # User info
    container_items.append(ui.TextDisplay(
        f"{ES('user')} **User:** {user} (`{user.id}`)\n"
        f"{ES('crown')} **Bot Owner:** {'Yes' if user.id == (bot.owner_id or 1313882631464550506) else 'No'}"
    ))

    container_items.append(ui.Separator())

    # Guild info
    if guild:
        container_items.append(ui.TextDisplay(
            f"{ES('server')} **Server:** {guild.name} (`{guild.id}`)\n"
            f"{ES('members')} **Members:** {guild.member_count}\n"
            f"{ES('channel')} **Channel:** #{channel.name} (`{channel.id}`)"
        ))
    else:
        container_items.append(ui.TextDisplay(
            f"{ES('info')} **DM Channel** — no guild"
        ))

    container_items.append(ui.Separator())

    # Message content (truncated)
    raw_content = _truncate(ctx.message.content, 500)
    container_items.append(ui.TextDisplay(
        f"{ES('dot')} **Message:**\n```\n{raw_content}\n```"
    ))

    # Jump link if available
    try:
        jump = ctx.message.jump_url
        container_items.append(ui.ActionRow(
            ui.Button(
                label="Jump to Message",
                style=discord.ButtonStyle.link,
                url=jump,
            )
        ))
    except Exception:
        pass

    container_items.append(ui.Separator(visible=False))
    container_items.append(ui.TextDisplay(
        f"-# <t:{_utcnow_ts()}:F> • <t:{_utcnow_ts()}:R>"
    ))

    view.add_item(_make_container(*container_items))
    return view


def _guild_join_view(bot: commands.Bot, guild: discord.Guild) -> ui.LayoutView:
    """Container for guild join event."""
    view = ui.LayoutView(timeout=None)

    owner = guild.owner
    owner_text = f"{owner} (`{owner.id}`)" if owner else f"`{guild.owner_id}`"

    # Try get guild icon
    icon_url = guild.icon.url if guild.icon else bot.user.display_avatar.url

    bot_count   = sum(1 for m in guild.members if m.bot)
    human_count = guild.member_count - bot_count if guild.member_count else 0

    header_text = ui.TextDisplay(
        f"## {ES('join')} Joined a New Server\n"
        f"**{guild.name}**"
    )

    try:
        section = ui.Section(
            header_text,
            accessory=ui.Thumbnail(
                media=discord.UnfurledMediaItem(url=icon_url),
                description=guild.name,
            ),
        )
        container_items = [section, ui.Separator()]
    except Exception:
        container_items = [header_text, ui.Separator()]

    container_items.append(ui.TextDisplay(
        f"{ES('server')} **Server ID:** `{guild.id}`\n"
        f"{ES('crown')} **Owner:** {owner_text}\n"
        f"{ES('members')} **Members:** {guild.member_count}\n"
        f"{ES('user')} **Humans:** {human_count}\n"
        f"{ES('bots')} **Bots:** {bot_count}"
    ))

    container_items.append(ui.Separator())

    created_ts = int(guild.created_at.timestamp())
    container_items.append(ui.TextDisplay(
        f"{ES('boost')} **Boost Level:** Tier {guild.premium_tier} "
        f"({guild.premium_subscription_count or 0} boosts)\n"
        f"{ES('clock')} **Created:** <t:{created_ts}:R>\n"
        f"{ES('online')} **Total Bot Guilds Now:** `{len(bot.guilds)}`"
    ))

    container_items.append(ui.Separator(visible=False))
    container_items.append(ui.TextDisplay(
        f"-# Joined at <t:{_utcnow_ts()}:F>"
    ))

    view.add_item(_make_container(*container_items))
    return view


def _guild_leave_view(bot: commands.Bot, guild: discord.Guild) -> ui.LayoutView:
    """Container for guild leave event."""
    view = ui.LayoutView(timeout=None)

    owner = guild.owner
    owner_text = f"{owner} (`{owner.id}`)" if owner else f"`{guild.owner_id}`"

    icon_url = guild.icon.url if guild.icon else bot.user.display_avatar.url

    header_text = ui.TextDisplay(
        f"## {ES('leave')} Left a Server\n"
        f"**{guild.name}**"
    )

    try:
        section = ui.Section(
            header_text,
            accessory=ui.Thumbnail(
                media=discord.UnfurledMediaItem(url=icon_url),
                description=guild.name,
            ),
        )
        container_items = [section, ui.Separator()]
    except Exception:
        container_items = [header_text, ui.Separator()]

    container_items.append(ui.TextDisplay(
        f"{ES('server')} **Server ID:** `{guild.id}`\n"
        f"{ES('crown')} **Owner:** {owner_text}\n"
        f"{ES('members')} **Last Member Count:** {guild.member_count or 'Unknown'}"
    ))

    container_items.append(ui.Separator())

    container_items.append(ui.TextDisplay(
        f"{ES('online')} **Total Bot Guilds Now:** `{len(bot.guilds)}`"
    ))

    container_items.append(ui.Separator(visible=False))
    container_items.append(ui.TextDisplay(
        f"-# Left at <t:{_utcnow_ts()}:F>"
    ))

    view.add_item(_make_container(*container_items))
    return view


def _error_log_view(
    bot: commands.Bot,
    ctx: commands.Context,
    error: Exception,
    tb: str,
) -> ui.LayoutView:
    """Container for command error event."""
    view = ui.LayoutView(timeout=None)

    cmd_name = ctx.command.qualified_name if ctx.command else "Unknown"

    header_text = ui.TextDisplay(
        f"## {ES('warning')} Command Error\n"
        f"-# `{cmd_name}`"
    )

    try:
        section = ui.Section(
            header_text,
            accessory=ui.Thumbnail(
                media=discord.UnfurledMediaItem(url=ctx.author.display_avatar.url),
                description=str(ctx.author),
            ),
        )
        container_items = [section, ui.Separator()]
    except Exception:
        container_items = [header_text, ui.Separator()]

    container_items.append(ui.TextDisplay(
        f"{ES('user')} **User:** {ctx.author} (`{ctx.author.id}`)\n"
        f"{ES('server')} **Server:** {ctx.guild.name if ctx.guild else 'DM'} "
        f"(`{ctx.guild.id if ctx.guild else 'N/A'}`)\n"
        f"{ES('channel')} **Channel:** #{ctx.channel.name if hasattr(ctx.channel, 'name') else 'DM'}"
    ))

    container_items.append(ui.Separator())

    container_items.append(ui.TextDisplay(
        f"{ES('error')} **Error Type:** `{type(error).__name__}`\n"
        f"{ES('dot')} **Message:**\n```\n{_truncate(str(error), 500)}\n```"
    ))

    container_items.append(ui.Separator())

    container_items.append(ui.TextDisplay(
        f"{ES('trace')} **Traceback:**\n```py\n{_truncate(tb, 1500)}\n```"
    ))

    # Jump link
    try:
        container_items.append(ui.ActionRow(
            ui.Button(
                label="Jump to Message",
                style=discord.ButtonStyle.link,
                url=ctx.message.jump_url,
            )
        ))
    except Exception:
        pass

    container_items.append(ui.Separator(visible=False))
    container_items.append(ui.TextDisplay(
        f"-# <t:{_utcnow_ts()}:F>"
    ))

    view.add_item(_make_container(*container_items))
    return view


def _ready_view(bot: commands.Bot) -> ui.LayoutView:
    """Container for bot ready event."""
    view = ui.LayoutView(timeout=None)

    total_users = sum(g.member_count or 0 for g in bot.guilds)

    header_text = ui.TextDisplay(
        f"## {ES('online')} {BOT_NAME} is Online\n"
        f"-# Bot is now fully ready & operational"
    )

    try:
        section = ui.Section(
            header_text,
            accessory=ui.Thumbnail(
                media=discord.UnfurledMediaItem(url=bot.user.display_avatar.url),
                description=str(bot.user),
            ),
        )
        container_items = [section, ui.Separator()]
    except Exception:
        container_items = [header_text, ui.Separator()]

    container_items.append(ui.TextDisplay(
        f"{ES('user')} **Bot:** {bot.user} (`{bot.user.id}`)\n"
        f"{ES('server')} **Guilds:** `{len(bot.guilds)}`\n"
        f"{ES('members')} **Total Users:** `{total_users}`\n"
        f"{ES('command')} **Loaded Cogs:** `{len(bot.cogs)}`\n"
        f"{ES('dot')} **Commands:** `{len(bot.commands)}`"
    ))

    container_items.append(ui.Separator())

    container_items.append(ui.TextDisplay(
        f"{ES('online')} **Latency:** `{round(bot.latency * 1000)}ms`\n"
        f"{ES('clock')} **Started:** <t:{_utcnow_ts()}:F>"
    ))

    view.add_item(_make_container(*container_items))
    return view


# ═══════════════════════════════════════════════════════════════
#  🚀  WEBHOOK SENDER
# ═══════════════════════════════════════════════════════════════

# Cache: webhook_url -> resolved discord.abc.Messageable (or False if
# unresolvable). Populated once per process so we don't call
# webhook.fetch() on every single log message.
_channel_cache: dict[str, object] = {}


async def _send_webhook(
    session: aiohttp.ClientSession,
    webhook_url: str,
    view: ui.LayoutView,
    bot: commands.Bot,
):
    """
    Send a LayoutView (Components V2) as a log message.

    IMPORTANT: Discord does NOT render custom emojis (guild or
    Application) inside messages sent via discord.Webhook.from_url()
    — a bare webhook has no bot/application identity attached, so
    Discord falls back to showing ":name:" as plain text. This is a
    platform limitation, not a bug in emojis.json/NIXO_STUDIO.emojis.

    Fix: resolve the webhook's channel ONCE (cached) and send through
    the BOT's own authenticated connection (channel.send) instead.
    This runs as a real message from the bot's application, so
    Application emojis (and any emoji the bot has access to) render
    correctly.

    Falls back to the raw webhook send (text/embeds still work, just
    without custom emoji) if the bot can't reach the channel — e.g.
    the webhook posts into a server the bot isn't in.
    """
    if not webhook_url:
        return

    try:
        webhook = discord.Webhook.from_url(webhook_url, session=session, client=bot)

        channel = _channel_cache.get(webhook_url)
        if channel is None:  # not cached yet this process
            try:
                fetched = await webhook.fetch()
                channel = bot.get_channel(fetched.channel_id) if fetched.channel_id else None
                if channel is None and fetched.channel_id:
                    channel = await bot.fetch_channel(fetched.channel_id)
            except Exception:
                channel = None
            _channel_cache[webhook_url] = channel if channel is not None else False

        if channel:
            # Bot-authenticated send — Application emojis render correctly.
            await channel.send(view=view)
            return

        # Fallback: bot can't see that channel (e.g. different server) —
        # send via the raw webhook. Custom emojis will show as plain
        # text (":name:") in this path; everything else still works.
        await webhook.send(
            view=view,
            username=BOT_NAME,
            avatar_url=bot.user.display_avatar.url if bot.user else None,
        )
    except Exception as e:
        print(f"[WebhookLogger] Failed to send: {e}")


# ═══════════════════════════════════════════════════════════════
#  🛡️  COG
# ═══════════════════════════════════════════════════════════════

class WebhookLogger(commands.Cog):
    """Global webhook logging — commands, joins, leaves, errors."""

    def __init__(self, bot: commands.Bot):
        self.bot     = bot
        self.session: aiohttp.ClientSession | None = None
        self._ready_sent = False

    async def cog_load(self):
        self.session = aiohttp.ClientSession()

    async def cog_unload(self):
        if self.session and not self.session.closed:
            await self.session.close()

    # ── Listeners ────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_ready(self):
        # Send ready log only once per process
        if self._ready_sent:
            return
        self._ready_sent = True

        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession()

        view = _ready_view(self.bot)
        await _send_webhook(self.session, WEBHOOK_READY, view, self.bot)

    @commands.Cog.listener()
    async def on_command_completion(self, ctx: commands.Context):
        """Fires after every successful command."""
        if ctx.author.bot:
            return

        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession()

        view = _command_log_view(self.bot, ctx)
        await _send_webhook(self.session, WEBHOOK_COMMANDS, view, self.bot)

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession()

        view = _guild_join_view(self.bot, guild)
        await _send_webhook(self.session, WEBHOOK_GUILD_JOIN, view, self.bot)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession()

        view = _guild_leave_view(self.bot, guild)
        await _send_webhook(self.session, WEBHOOK_GUILD_LEAVE, view, self.bot)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: Exception):
        """Log unhandled errors (CommandNotFound etc. excluded)."""
        # Skip noisy/handled errors
        skip_types = (
            commands.CommandNotFound,
            commands.MissingRequiredArgument,
            commands.MissingPermissions,
            commands.BotMissingPermissions,
            commands.MemberNotFound,
            commands.RoleNotFound,
            commands.BadArgument,
            commands.CheckFailure,
            commands.CommandOnCooldown,
            commands.NoPrivateMessage,
            commands.NotOwner,
        )

        # Unwrap CommandInvokeError to get the real exception
        original = getattr(error, "original", error)

        if isinstance(error, skip_types):
            return

        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession()

        tb = "".join(
            traceback.format_exception(type(original), original, original.__traceback__)
        )

        view = _error_log_view(self.bot, ctx, original, tb)
        await _send_webhook(self.session, WEBHOOK_ERRORS, view, self.bot)


async def setup(bot: commands.Bot):
    await bot.add_cog(WebhookLogger(bot))