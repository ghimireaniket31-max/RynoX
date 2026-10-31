"""
core/__init__.py
Small compatibility layer so cogs ported from ZyroX-CV2-AIO (MIT, (c) 2026 CodeX Devs)
run unchanged inside RynoX.

ZyroX's cogs do ``from core import Cog, zyrox, Context``.  RynoX does not need ZyroX's
custom bot/cog/context subclasses, so these names simply point at the stock discord.py ones.
"""
from discord.ext import commands

# Stock discord.py classes – drop-in replacements for ZyroX's thin subclasses.
Context = commands.Context
Cog = commands.Cog
zyrox = commands.Bot   # type alias only (used for annotations such as ``bot: zyrox``)

__all__ = ("Cog", "Context", "zyrox")
