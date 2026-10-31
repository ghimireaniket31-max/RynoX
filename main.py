"""
main.py - RynoX Bot
"""

import discord
from discord import app_commands
from discord.ext import commands, tasks
import os
import time
import asyncio
import hashlib
import json
import traceback
from pathlib import Path
from dotenv import load_dotenv
from utils import emojis as E
from utils.developers import DEVELOPER_IDS

load_dotenv()

owners = set(int(i.strip()) for i in os.getenv("OWNER_IDS", "").split(",") if i.strip().isdigit())

DEFAULT_PREFIX = os.getenv("BOT_PREFIX", ".")
BOT_NAME       = "RynoX"
WEBSITE        = os.getenv("WEBSITE", "")
SUPPORT        = os.getenv("SUPPORT_SERVER", "https://discord.gg/TKDHTJ85Ta")
STATUS_PAGE    = os.getenv("STATUS_PAGE", "")
INVITE_URL     = os.getenv("INVITE_URL", "https://discord.com/oauth2/authorize?client_id=1565750430477058098&permissions=8&integration_type=0&scope=bot+applications.commands")
OWNER_IDS = owners | set(DEVELOPER_IDS)     # .env OWNER_IDS + every developer


# ═══════════════════════════════════════════════════════════════
#  DYNAMIC PREFIX FUNCTION
# ═══════════════════════════════════════════════════════════════

def _get_prefix(bot, message: discord.Message):
    """
    Guild-specific prefix support.
    Falls back to DEFAULT_PREFIX if not set or in DMs.
    """
    if not message.guild:
        return DEFAULT_PREFIX

    try:
        from cogs.prefix import get_prefix
        return get_prefix(message.guild.id)
    except Exception:
        return DEFAULT_PREFIX


# ═══════════════════════════════════════════════════════════════
#  BOT CLASS
# ═══════════════════════════════════════════════════════════════

def _slash_signature(cmd) -> dict:
    """Small, stable description of a slash command (used to detect changes between runs)."""
    sig = {"name": cmd.name, "description": cmd.description}
    if isinstance(cmd, app_commands.Group):
        sig["subcommands"] = [_slash_signature(c) for c in cmd.commands]
    else:
        sig["params"] = [(p.name, p.description, p.required, str(p.type)) for p in cmd.parameters]
    return sig


class NixoStudio(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(
            command_prefix   = _get_prefix,       # ← DYNAMIC PREFIX
            intents          = intents,
            help_command     = None,
            case_insensitive = True,
            allowed_mentions = discord.AllowedMentions(
                everyone     = False,
                users        = False,
                roles        = False,
                replied_user = False,
            ),
        )
        self.start_time      = time.time()
        self.BOT_NAME        = BOT_NAME
        self.DEFAULT_PREFIX  = DEFAULT_PREFIX
        self.WEBSITE         = WEBSITE
        self.SUPPORT_SERVER  = SUPPORT
        self.STATUS_PAGE     = STATUS_PAGE
        self.INVITE_URL      = INVITE_URL
        self.OWNER_IDS       = OWNER_IDS

        # Rotating Status List
        self.status_list = [
            f"Powered by RynoX development | {DEFAULT_PREFIX}help",
            "RynoX - Control Everything",
        ]
        self.status_index = 0

    async def setup_hook(self):
        cogs = [
            "cogs.prefix",             # ← LOAD FIRST (prefix + ignore system)
            "cogs.ping",
            "cogs.stats",
            "cogs.moderation",
            "cogs.purge",
            "cogs.role",
            "cogs.channelinfo",
            "cogs.general",
            "cogs.list_cmds",
            "cogs.roleinfo",
            "cogs.serverinfo",
            "cogs.ticket",
            "cogs.userinfo",
            "cogs.embeds",
            "cogs.devjsk",
            "cogs.noprefix",
            "cogs.guild_join",
            "cogs.mention",
            "cogs.giveaway",
            "cogs.welcome",
            "cogs.tracker",
            "cogs.autorole",
            "cogs.autoresponder",
            "cogs.autoreact",
            "cogs.reactionrole",
            "cogs.logging",
            "cogs.antinuke_core",
            "cogs.antinuke_modules",
            "cogs.automod",
            "cogs.honeypot",
            "cogs.help",
            "cogs.premium",
            "cogs.warn",               # warn system + escalation
            "cogs.webhook_logger",
            "cogs.extended",           # commands ported from ZyroX (load last)
        ]

        for cog in cogs:
            try:
                await self.load_extension(cog)
                print(f"✅  Loaded  : {cog}")
            except Exception as err:
                print(f"❌ Failed  : {cog} — {err}")

        # slash (hybrid) commands only exist on Discord after a sync
        self.tree.on_error = self.on_app_command_error
        await self._sync_slash_commands()

    # ═══════════════════════════════════════════════════════
    #  SLASH COMMANDS
    # ═══════════════════════════════════════════════════════

    async def is_owner(self, user) -> bool:
        """`commands.is_owner()` passes for every configured owner/developer, and still for the
        Discord application's own owner/team (discord.py's default behaviour)."""
        if user.id in OWNER_IDS:
            return True
        return await super().is_owner(user)

    async def _sync_slash_commands(self):
        """
        Register the slash commands with Discord on startup.
        The sync is skipped when nothing changed since the last successful one
        (stored in db/slash_sync.hash) so restarts don't hit Discord's rate limit.
        """
        marker = Path("db") / "slash_sync.hash"
        try:
            top = self.tree.get_commands()
            try:
                raw = json.dumps(
                    [_slash_signature(c) for c in top] + [self.application_id],
                    sort_keys=True, default=str,
                )
                digest = hashlib.sha256(raw.encode()).hexdigest()
            except Exception:
                digest = None                      # can't fingerprint -> always sync

            if digest and marker.exists() and marker.read_text().strip() == digest:
                print(f"ℹ️  [Slash] {len(top)} slash commands already synced")
                return

            synced = await self.tree.sync()
            if digest:
                marker.parent.mkdir(exist_ok=True)
                marker.write_text(digest)
            print(f"✅  Synced  : {len(synced)} slash commands")
        except Exception as err:
            print(f"❌ Slash sync failed — {err}")
            print("   (check the command names/descriptions of the newest hybrid commands, or run `.dev sync`)")

    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Errors from pure slash commands - tell the user instead of 'application did not respond'."""
        from utils.ui import denied_container

        if isinstance(error, app_commands.MissingPermissions):
            text = "You don't have permission to use this command!"
        elif isinstance(error, app_commands.CommandOnCooldown):
            text = f"Command on cooldown! Try again in `{error.retry_after:.1f}s`"
        elif isinstance(error, app_commands.CheckFailure):
            text = "You can't use this command here."
        else:
            traceback.print_exception(type(error), error, error.__traceback__)
            text = "Something went wrong while running this command."

        try:
            payload = denied_container(text)
            if interaction.response.is_done():
                await interaction.followup.send(**payload, ephemeral=True)
            else:
                await interaction.response.send_message(**payload, ephemeral=True)
        except Exception:
            pass

    async def on_ready(self):
        print(f"\n{'=' * 45}")
        print(f"  🟢 {BOT_NAME} is Online!")
        print(f"  User    : {self.user}")
        print(f"  Guilds  : {len(self.guilds)}")
        print(f"  Users   : {sum(g.member_count or 0 for g in self.guilds)}")
        print(f"{'=' * 45}\n")

        if not self.rotate_status.is_running():
            self.rotate_status.start()

    # ═══════════════════════════════════════════════════════
    #  ROTATING STATUS
    # ═══════════════════════════════════════════════════════

    @tasks.loop(seconds=10)
    async def rotate_status(self):
        try:
            await self.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.watching,
                    name=self.status_list[self.status_index],
                )
            )
            self.status_index = (self.status_index + 1) % len(self.status_list)
        except Exception as e:
            print(f"Status error: {e}")

    @rotate_status.before_loop
    async def before_rotate_status(self):
        await self.wait_until_ready()

    # ═══════════════════════════════════════════════════════
    #  ON_MESSAGE  —  Ignore System + Category Shortcut
    # ═══════════════════════════════════════════════════════

    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        # ── IGNORE CHECK ──
        # Ignored channels mein bot bilkul respond nahi karega
        # Na prefix commands, na noprefix, kuch bhi nahi
        if message.guild:
            try:
                from cogs.prefix import is_ignored
                if is_ignored(message.guild.id, message.channel.id):
                    # Sirf ignore/unignore/ignorelist commands allow karo
                    ctx = await self.get_context(message)
                    if ctx.command and ctx.command.qualified_name in (
                        "ignore", "unignore", "ignorelist"
                    ):
                        return await self.process_commands(message)

                    # NTHING RESPOND!
                    return
            except ImportError:
                pass

        ctx = await self.get_context(message)

        # ── Category shortcut ──
        if ctx.prefix and not ctx.command:
            try:
                from utils.category_help import get_category, CategoryHelpView

                raw = message.content[len(ctx.prefix):].strip()
                query = raw.lower().split()[0] if raw else ""

                if query:
                    cat_key, cat_data = get_category(query)
                    if cat_key and cat_data:
                        view = CategoryHelpView(
                            ctx           = ctx,
                            category_key  = cat_key,
                            category_data = cat_data,
                            bot_name      = self.BOT_NAME,
                            prefix        = ctx.prefix,
                        )
                        return await message.channel.send(view=view)
            except Exception:
                pass

        await self.process_commands(message)

    # ═══════════════════════════════════════════════════════
    #  ERROR HANDLER
    # ═══════════════════════════════════════════════════════

    async def on_command_error(self, ctx, error):
        from utils.ui import denied_container
        from utils.cmd_help import cmd_usage_view

        if isinstance(error, commands.MissingRequiredArgument):
            view = cmd_usage_view(ctx.prefix, ctx.command.name)
            if view:
                return await ctx.send(view=view)
            return await ctx.send(
                **denied_container(f"Missing argument: `{error.param.name}`")
            )

        if isinstance(error, commands.CommandNotFound):
            return

        if isinstance(error, commands.MissingPermissions):
            return await ctx.send(**denied_container(
                "You don't have permission to use this command!"
            ))

        if isinstance(error, commands.BotMissingPermissions):
            return await ctx.send(**denied_container(
                "I don't have the required permissions!"
            ))

        if isinstance(error, commands.MemberNotFound):
            return await ctx.send(**denied_container(
                "Member not found! Please mention a valid member."
            ))

        if isinstance(error, commands.RoleNotFound):
            return await ctx.send(**denied_container(
                "Role not found! Please mention a valid role."
            ))

        if isinstance(error, commands.BadArgument):
            view = cmd_usage_view(ctx.prefix, ctx.command.name)
            if view:
                return await ctx.send(view=view)
            return await ctx.send(
                **denied_container(f"Invalid argument: `{error}`")
            )

        if isinstance(error, commands.CheckFailure):
            return await ctx.send(**denied_container(
                "You don't have permission to use this command!"
            ))

        if isinstance(error, commands.CommandOnCooldown):
            return await ctx.send(**denied_container(
                f"Command on cooldown! Try again in `{error.retry_after:.1f}s`"
            ))

        # Anything else raised by a slash command: log it and answer the user
        # (otherwise Discord only shows "The application did not respond").
        if getattr(ctx, "interaction", None) is not None:
            original = getattr(error, "original", error)
            traceback.print_exception(type(original), original, original.__traceback__)
            try:
                await ctx.send(
                    **denied_container("Something went wrong while running this command."),
                    ephemeral=True,
                )
            except Exception:
                pass


# ═══════════════════════════════════════════════════════════════
#  AUTO EMOJI UPLOAD + RUN
# ═══════════════════════════════════════════════════════════════

async def _auto_upload_emojis():
    """
    Runs the application emoji upload once (on first start).
    After emojis.uploaded.json is populated this is instant —
    it just skips all already-uploaded keys.
    Triggered automatically before bot.start() every run.
    """
    uploaded_path = Path("emojis.uploaded.json")
    try:
        uploaded_data = json.loads(uploaded_path.read_text(encoding="utf-8")) if uploaded_path.exists() else {}
        definitions = json.loads(Path("emojis.json").read_text(encoding="utf-8"))
        required = {k for k, v in definitions.items() if not k.startswith("_") and isinstance(v, str) and v.startswith("<")}
        local_path = Path("emojis.local.json")        # emojis created from local image files
        if local_path.exists():
            local_defs = json.loads(local_path.read_text(encoding="utf-8"))
            required |= {k for k in local_defs if not k.startswith("_")}
        cached = {k for k, v in uploaded_data.items() if isinstance(v, dict) and v.get("id")}
        if required and required.issubset(cached):
            print("✅ [Emojis] Application emoji cache is complete — skipping upload.")
            return
        print(f"ℹ️  [Emojis] Emoji cache incomplete ({len(cached)}/{len(required)}); syncing…")
    except Exception:
        uploaded_data = {}

    print("⏳ [Emojis] First-time emoji upload starting…")
    try:
        # Import and run the upload coroutine
        import sys
        sys.path.insert(0, str(Path(__file__).parent))
        from scripts.upload_application_emojis import run as _upload_run
        await _upload_run()
        # Reload the in-memory emoji map so new IDs are live immediately
        from NIXO_STUDIO.emojis import E as _emgr
        _emgr.reload()
        print("✅ [Emojis] Upload complete — bot will now use Application emoji IDs.")
    except Exception as e:
        print(f"⚠️  [Emojis] Upload failed ({e}), using fallback guild emoji IDs.")


async def _start():
    """Async entry point: upload emojis then start the bot."""
    await _auto_upload_emojis()
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("❌ No DISCORD_TOKEN found in .env!")
        return

    await bot.start(token)


bot = NixoStudio()

if __name__ == "__main__":
    try:
        asyncio.run(_start())
    except KeyboardInterrupt:
        print("\n⛔ Bot stopped.")