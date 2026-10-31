# ╔══════════════════════════════════════════════════════════════════╗
# ║  cogs/extended - commands ported from ZyroX-CV2-AIO               ║
# ║  Original code: MIT License, (c) 2026 CodeX Devs (LICENSE-ZyroX)  ║
# ╚══════════════════════════════════════════════════════════════════╝
"""
cogs/extended/__init__.py
Loader for the commands ported from ZyroX-CV2-AIO.

* every ``zx_*.py`` module in this package is a ZyroX cog with the commands that already exist in
  RynoX removed (checked by name and alias) and its databases moved to ``db/zx/``
* each module is loaded on its own - one broken/missing dependency only disables that module
* ``attach`` entries: the ZyroX ``clear`` / ``role`` groups are hidden carriers; their subcommands are
  moved onto RynoX's real ``clear`` / ``role`` groups once the cog is loaded
"""

import importlib
import os
import traceback

from discord.ext import commands

from utils import zx_schema
from utils.developers import DEVELOPER_IDS

# (module, [cog classes], [(carrier group, real RynoX group)])
MODULES = [
    ('zx_Birthday', ['Birthdays'], []),
    ('zx_Games', ['Games'], []),
    ('zx_Invc', ['Invcrole'], []),
    ('zx_Media', ['Media'], []),
    ('zx_ai', ['AI'], []),
    ('zx_blackjack', ['Blackjack'], []),
    ('zx_blacklist', ['Blacklist'], []),
    ('zx_block', ['Block'], []),
    ('zx_booster', ['Booster'], []),
    ('zx_calc', ['calculator'], []),
    ('zx_counting', ['Counting'], []),
    ('zx_customrole', ['Customrole'], []),
    ('zx_dms', ['StaffDMCog'], []),
    ('zx_emergency', ['Emergency'], []),
    ('zx_encryption', ['encryption'], []),
    ('zx_extra', ['Extra'], []),
    ('zx_fastgreet', ['FastGreet'], []),
    ('zx_filters', ['FilterCog'], []),
    ('zx_fun', ['Fun'], []),
    ('zx_general', ['General'], []),
    ('zx_image', ['ImageCommands'], []),
    ('zx_j2c', ['JoinToCreate'], []),
    ('zx_jail', ['Jail'], []),
    ('zx_joindm', ['joindm'], []),
    ('zx_leveling', ['Leveling'], []),
    ('zx_map', ['Map'], []),
    ('zx_music', ['Music'], []),
    ('zx_nightmode', ['Nightmode'], []),
    ('zx_nitro', ['Nitro'], []),
    ('zx_notify', ['NotifCommands'], []),
    ('zx_owner', ['Owner', 'Badges'], []),
    ('zx_owner2', ['Global'], []),
    ('zx_reactionroles', ['ReactionRoles'], []),
    ('zx_slots', ['Slots'], []),
    ('zx_status', ['Status'], []),
    ('zx_steal', ['Steal'], []),
    ('zx_stickymessage', ['StickyMessage'], []),
    ('zx_timer', ['Timer'], []),
    ('zx_tracking', ['Tracking'], []),
    ('zx_translate', ['TranslateCog'], []),
    ('zx_vanityroles', ['VanityRoles'], []),
    ('zx_verification', ['Verification'], []),
    ('zx_voice', ['Voice'], []),
    ('zx_youtube', ['Youtube'], []),
    ('zx_message', ['Message'], [('__zx_clear', 'clear')]),
    ('zx_moderation', ['Moderation'], []),
    ('zx_role', ['Role'], [('__zx_role', 'role')]),
    ('zx_topcheck', ['TopCheck'], []),
]

_ATTACHED = []     # (real group, subcommand) moved onto RynoX groups - undone in teardown()


def _attach(bot, carrier_name, real_name):
    carrier = bot.get_command(carrier_name)
    real = bot.get_command(real_name)
    if carrier is None or real is None or not isinstance(real, commands.GroupMixin):
        return 0
    moved = 0
    for sub in list(carrier.commands):
        carrier.remove_command(sub.name)
        sub.parent = real
        try:
            real.add_command(sub)
        except commands.CommandRegistrationError:
            continue          # RynoX already has it - keep RynoX's version
        _ATTACHED.append((real, sub))
        moved += 1
    bot.remove_command(carrier_name)   # the hidden carrier itself is never exposed
    return moved


async def _global_blacklist(ctx):
    """Bot-wide blacklist (users/guilds added with the ported ``blacklist`` command). Fails open."""
    if ctx.author.id in DEVELOPER_IDS:
        return True
    try:
        import aiosqlite
        zx_schema.ensure_all()
        async with aiosqlite.connect(zx_schema.ZX_DB_DIR + "/block.db") as db:
            cur = await db.execute("SELECT 1 FROM user_blacklist WHERE user_id = ?", (ctx.author.id,))
            if await cur.fetchone():
                return False
            if ctx.guild:
                cur = await db.execute("SELECT 1 FROM guild_blacklist WHERE guild_id = ?", (ctx.guild.id,))
                if await cur.fetchone():
                    return False
    except Exception:
        return True
    return True


async def setup(bot):
    zx_schema.ensure_all()
    os.makedirs(os.path.join(zx_schema.ZX_DB_DIR, "jsondb"), exist_ok=True)

    loaded = failed = 0
    for module, classes, attach in MODULES:
        try:
            mod = importlib.import_module(f"cogs.extended.{module}")
            for cname in classes:
                await bot.add_cog(getattr(mod, cname)(bot))
            for carrier, real in attach:
                _attach(bot, carrier, real)
            loaded += 1
        except Exception as exc:
            failed += 1
            print(f"   \u274c extended/{module}: {type(exc).__name__}: {exc}")
            if os.getenv("ZX_DEBUG"):
                traceback.print_exc()

    bot.add_check(_global_blacklist)
    print(f"   \u2705 extended: {loaded} modules loaded, {failed} failed")
    if failed and not os.getenv("ZX_DEBUG"):
        print("      (set ZX_DEBUG=1 for the full traceback; missing packages: pip install -r requirements.txt)")


async def teardown(bot):
    for real, sub in _ATTACHED:
        real.remove_command(sub.name)
    _ATTACHED.clear()
    bot.remove_check(_global_blacklist)
    # the ported cogs themselves are removed by discord.py when the extension is unloaded
