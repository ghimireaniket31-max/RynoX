"""
cogs/warn.py
Warn system with automatic escalation.

    3  warns  ->  24 hour mute (timeout)
    5  warns  ->  3 day mute   (timeout)
    10 warns  ->  permanent ban

The escalation fires when a member *reaches* one of those totals.  Clearing a member's warns
resets the count.  Every warn is stored with its moderator, reason and time (db/warns.db).
"""

import datetime
from pathlib import Path

import aiosqlite
import discord
from discord.ext import commands

from cogs.moderation import hierarchy_check, try_dm
from utils import emojis as E
from utils.cmd_help import cmd_usage_view
from utils.ui import denied_container, mod_action_container, action_container, info_container

DB_DIR  = Path("db")
DB_PATH = DB_DIR / "warns.db"

# total warns -> (action, seconds, human label)
ESCALATION = {
    3:  ("mute", 24 * 3600, "24 hours"),
    5:  ("mute", 3 * 86400, "3 days"),
    10: ("ban",  None,      "permanently"),
}


class Warn(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        DB_DIR.mkdir(exist_ok=True)
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS warns (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id     INTEGER NOT NULL,
                    user_id      INTEGER NOT NULL,
                    moderator_id INTEGER NOT NULL,
                    reason       TEXT,
                    created_at   INTEGER NOT NULL
                )
                """
            )
            await db.execute("CREATE INDEX IF NOT EXISTS idx_warns_gu ON warns (guild_id, user_id)")
            await db.commit()

    # ── storage helpers ──────────────────────────────────
    async def _add_warn(self, guild_id: int, user_id: int, moderator_id: int, reason: str | None) -> int:
        """Store a warn and return the member's new total."""
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO warns (guild_id, user_id, moderator_id, reason, created_at) VALUES (?, ?, ?, ?, ?)",
                (guild_id, user_id, moderator_id, reason, int(discord.utils.utcnow().timestamp())),
            )
            await db.commit()
            async with db.execute(
                "SELECT COUNT(*) FROM warns WHERE guild_id = ? AND user_id = ?", (guild_id, user_id)
            ) as cur:
                (total,) = await cur.fetchone()
        return total

    async def _get_warns(self, guild_id: int, user_id: int):
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT id, moderator_id, reason, created_at FROM warns "
                "WHERE guild_id = ? AND user_id = ? ORDER BY id DESC",
                (guild_id, user_id),
            ) as cur:
                return await cur.fetchall()

    async def _clear_warns(self, guild_id: int, user_id: int) -> int:
        async with aiosqlite.connect(DB_PATH) as db:
            cur = await db.execute(
                "DELETE FROM warns WHERE guild_id = ? AND user_id = ?", (guild_id, user_id)
            )
            await db.commit()
            return cur.rowcount

    # ── escalation ───────────────────────────────────────
    async def _escalate(self, ctx, member: discord.Member, total: int) -> list[str]:
        """Apply the mute / ban for ``total`` warns (if any). Returns extra result lines."""
        rule = ESCALATION.get(total)
        if rule is None:
            return []

        action, seconds, label = rule
        reason = f"Warn escalation: reached {total} warnings"

        if action == "mute":
            await try_dm(
                member,
                f"You have been **muted** in **{ctx.guild.name}** for **{label}**.\n"
                f"**Reason:** {reason}",
            )
            try:
                until = discord.utils.utcnow() + datetime.timedelta(seconds=seconds)
                await member.timeout(until, reason=f"[{ctx.author}] {reason}")
            except (discord.Forbidden, discord.HTTPException):
                return [f"Auto-mute ({label}) FAILED - check my permissions and role position"]
            return [f"Auto-mute : {label} ({total} warns)"]

        # permanent ban
        await try_dm(
            member,
            f"You have been **permanently banned** from **{ctx.guild.name}**.\n"
            f"**Reason:** {reason}",
        )
        try:
            await member.ban(reason=f"[{ctx.author}] {reason}", delete_message_days=0)
        except (discord.Forbidden, discord.HTTPException):
            return ["Auto-ban (permanent) FAILED - check my permissions and role position"]
        return [f"Auto-ban : permanent ({total} warns)"]

    # ── WARN ─────────────────────────────────────────────
    @commands.command(name="warn", aliases=["warnuser"])
    @commands.has_permissions(moderate_members=True)
    @commands.guild_only()
    async def warn(self, ctx, member: discord.Member = None, *, reason: str = None):
        """Warn a member. 3 warns = 24h mute, 5 = 3 day mute, 10 = permanent ban."""
        if member is None:
            return await ctx.send(view=cmd_usage_view(ctx.prefix, "warn"))

        if member == ctx.author:
            return await ctx.send(**denied_container("You cannot warn yourself!"))
        if member == ctx.guild.me:
            return await ctx.send(**denied_container("I cannot warn myself!"))
        if member.bot:
            return await ctx.send(**denied_container("You cannot warn a bot!"))

        ok, err = hierarchy_check(ctx, member)
        if not ok:
            return await ctx.send(**denied_container(err))

        total = await self._add_warn(ctx.guild.id, member.id, ctx.author.id, reason)

        dm_done = await try_dm(
            member,
            f"You have been **warned** in **{ctx.guild.name}**.\n"
            f"**Reason:** {reason or 'No reason provided'}\n"
            f"**Total warns:** {total}",
        )

        extra = [f"Total warns : `{total}`"]
        extra += await self._escalate(ctx, member, total)

        await ctx.send(
            **mod_action_container(
                action         = "User have been warned!",
                target_name    = str(member),
                moderator_name = ctx.author.name,
                reason         = reason,
                dm_done        = dm_done,
                extra_lines    = extra,
                bot_avatar     = self.bot.user.display_avatar.url,
            )
        )

    # ── WARNINGS (list) ──────────────────────────────────
    @commands.command(name="warnings", aliases=["warns", "warnlist"])
    @commands.has_permissions(moderate_members=True)
    @commands.guild_only()
    async def warnings(self, ctx, member: discord.Member = None):
        """Show a member's warns."""
        if member is None:
            return await ctx.send(view=cmd_usage_view(ctx.prefix, "warnings"))

        rows = await self._get_warns(ctx.guild.id, member.id)
        if not rows:
            return await ctx.send(
                **info_container(f"Warnings - {member}", "No warnings on record.")
            )

        lines = []
        for wid, mod_id, reason, ts in rows[:10]:
            lines.append(
                f"> **#{wid}** - <t:{ts}:R> by <@{mod_id}>\n> `{reason or 'No reason provided'}`"
            )
        more = f"\n*...and {len(rows) - 10} older warn(s)*" if len(rows) > 10 else ""

        await ctx.send(
            **info_container(
                f"Warnings - {member}  ({len(rows)} total)",
                "\n".join(lines) + more,
                thumbnail_url=member.display_avatar.url,
            )
        )

    # ── CLEARWARNS ───────────────────────────────────────
    @commands.command(name="clearwarns", aliases=["clearwarn", "clearwarnings"])
    @commands.has_permissions(moderate_members=True)
    @commands.guild_only()
    async def clearwarns(self, ctx, member: discord.Member = None):
        """Remove every warn from a member (resets escalation)."""
        if member is None:
            return await ctx.send(view=cmd_usage_view(ctx.prefix, "clearwarns"))

        removed = await self._clear_warns(ctx.guild.id, member.id)
        if removed == 0:
            return await ctx.send(**denied_container(f"{member} has no warnings to clear."))

        await ctx.send(
            **action_container(
                "Warnings cleared!",
                [
                    f"{E.TARGET}  {member}",
                    f"{E.MODERATOR} **Moderator:** {ctx.author.name}",
                    f"> **Removed :** `{removed}` warn(s)",
                ],
            )
        )


async def setup(bot):
    await bot.add_cog(Warn(bot))
