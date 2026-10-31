# ╔══════════════════════════════════════════════════════════════════╗
# ║                                                                  ║
# ║   ░█▀▀░█▀█░█▀▄░█▀▀░█░█   ░█▀▄░█▀▀░█░█░█▀▀                     ║
# ║   ░█░░░█░█░█░█░█▀▀░▄▀▄   ░█░█░█▀▀░▀▄▀░▀▀█                     ║
# ║   ░▀▀▀░▀▀▀░▀▀░░▀▀▀░▀░▀   ░▀▀░░▀▀▀░░▀░░▀▀▀                     ║
# ║                                                                  ║
# ║            © 2026 CodeX Devs — All Rights Reserved              ║
# ║                                                                  ║
# ║   discord  ──  https://discord.gg/codexdev                      ║
# ║   youtube  ──  https://youtube.com/@CodeXDevs                   ║
# ║   github   ──  https://github.com/RayExo                        ║
# ║                                                                  ║
# ╚══════════════════════════════════════════════════════════════════╝

import discord
from utils.emoji import CROSS, DENIED, TICK, ZWARNING
import asyncio
import datetime
import re
import typing
import typing as t
from typing import *
from utils.Tools import *
from core import Cog, zyrox, Context
from discord.ext.commands import Converter
from discord.ext import commands, tasks
from discord.ui import Button, View
from typing import Union, Optional
from utils import Paginator, DescriptionEmbedPaginator, FieldPagePaginator, TextPaginator
from typing import Union, Optional
from io import BytesIO
import requests
import aiohttp
import time
from datetime import datetime, timezone, timedelta
import sqlite3
from typing import *
from discord.utils import utcnow



time_regex = re.compile(r"(?:(\d{1,5})(h|s|m|d))+?")
time_dict = {"h": 3600, "s": 1, "m": 60, "d": 86400}


def convert(argument):
  args = argument.lower()
  matches = re.findall(time_regex, args)
  time = 0
  for key, value in matches:
    try:
      time += time_dict[value] * float(key)
    except KeyError:
      raise commands.BadArgument(
        f"{value} is an invalid time key! h|m|s|d are valid arguments")
    except ValueError:
      raise commands.BadArgument(f"{key} is not a number!")
  return round(time)

async def do_removal(ctx, limit, predicate, *, before=None, after=None):
    if limit > 2000:
        return await ctx.error(f"Too many messages to search given ({limit}/2000)")

    if before is None:
        before = ctx.message
    else:
        before = discord.Object(id=before)

    if after is not None:
        after = discord.Object(id=after)

    try:
        deleted = await ctx.channel.purge(limit=limit, before=before, after=after, check=predicate)
    except discord.Forbidden as e:
        return await ctx.error("I do not have permissions to delete messages.")
    except discord.HTTPException as e:
        return await ctx.error(f"Error: {e} (try a smaller search?)")

    spammers = Counter(m.author.display_name for m in deleted)
    deleted = len(deleted)
    messages = [f'{TICK}> | {deleted} message{" was" if deleted == 1 else "s were"} removed.']
    if deleted:
        messages.append("")
        spammers = sorted(spammers.items(), key=lambda t: t[1], reverse=True)
        messages.extend(f"**{name}**: {count}" for name, count in spammers)

    to_send = "\n".join(messages)

    if len(to_send) > 2000:
        await ctx.send(f"{TICK}> | Successfully removed {deleted} messages.", delete_after=7)
    else:
        await ctx.send(to_send, delete_after=7)




class Moderation(commands.Cog, name="ZXModeration"):

  def __init__(self, bot):
    self.bot = bot
    self.color = 0xFFFFFF
    self.sniped = {}

  def convert(self, time):
    pos = ["s", "m", "h", "d"]

    time_dict = {"s": 1, "m": 60, "h": 3600, "d": 3600 * 24}
    unit = time[-1]
    if unit not in pos:
      return -1
    try:
      val = int(time[:-1])
    except:
      return -2
    return val * time_dict[unit]



  @commands.command()
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  async def enlarge(self, ctx,  emoji: Union[discord.Emoji, discord.PartialEmoji, str]):
    url = emoji.url
    await ctx.send(url)







          

  @commands.hybrid_command(name="give",
                    help="Gives the mentioned user a role.",
                    usage="give <user> <role>",
                    aliases=["addrole"])
  @blacklist_check()
  @ignore_check()
  @top_check()
  @commands.cooldown(1, 10, commands.BucketType.user)
  @commands.has_permissions(manage_roles=True)
  @commands.bot_has_permissions(manage_roles= True)
  async def give(self, ctx, member: discord.Member, *, role: discord.Role):
    if not ctx.guild.me.guild_permissions.manage_roles:
        return await ctx.send(f"{DENIED} I don't have permission to manage roles!")

    if role >= ctx.guild.me.top_role:
        error = discord.Embed(
            color=self.color,
            description="I can't manage roles for a user with a higher or equal role!"
        )

        error.set_author(name="Error")
        error.set_footer(text=f"Requested by {ctx.author}",
                        icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        return await ctx.send(embed=error)

    if ctx.author != ctx.guild.owner and ctx.author.top_role <= member.top_role:
        error = discord.Embed(
            color=self.color,
            description="You can't manage roles for a user with a higher or equal role than yours!"
        )
        error.set_author(name="Access Denied")
        error.set_footer(text=f"Requested by {ctx.author}",
                        icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        return await ctx.send(embed=error)

    try:
        if role not in member.roles:
            await member.add_roles(role, reason=f"Role added by {ctx.author} (ID: {ctx.author.id})")
            success = discord.Embed(
                color=self.color,
                description=f"Successfully **added** role {role.name} to {member.mention}."
            )
            success.set_author(name="Role Added")
            success.set_footer(text=f"Requested by {ctx.author}",
                        icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        else:
            await member.remove_roles(role, reason=f"Role removed by {ctx.author} (ID: {ctx.author.id})")
            success = discord.Embed(
                color=self.color,
                description=f"Successfully **removed** role {role.name} from {member.mention}."
            )
            success.set_author(name="Role Removed")
            success.set_footer(text=f"Requested by {ctx.author}",
                        icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        await ctx.send(embed=success)
    except discord.Forbidden:
        error = discord.Embed(
            color=self.color,
            description=f"{ZWARNING} I don't have permission to manage roles for this user!"
        )
        await ctx.send(embed=error)
    except Exception as e:
        error = discord.Embed(
            color=self.color,
            description=f"{ZWARNING} An unexpected error occurred: {str(e)}"
        )
        await ctx.send(embed=error)







        


  @commands.hybrid_command(name="clone", help="Clones a channel.")
  @blacklist_check()
  @ignore_check()
  @commands.has_permissions(manage_channels=True)
  async def clone(self, ctx: commands.Context, channel: discord.TextChannel):
    
    if not ctx.guild.me.guild_permissions.manage_channels:
        error = discord.Embed(
            color=self.color,
            description="I don't have permission to manage channels!"
        )
        error.set_author(name="Error")
        error.set_footer(text=f"Requested by {ctx.author}",
                        icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        return await ctx.send(embed=error)


    try:
        
        await channel.clone()
        success = discord.Embed(
            color=self.color,
            description=f"{channel.name} has been successfully cloned"
        )
        success.set_author(name="Success")
        success.set_footer(text=f"Requested by {ctx.author}",
                        icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        await ctx.send(embed=success)
    except discord.Forbidden:
        error = discord.Embed(
            color=self.color,
            description="I don't have permission to clone channels!"
        )
        error.set_author(name="Error")
        await ctx.send(embed=error)
    except Exception as e:
        error = discord.Embed(
            color=self.color,
            description=f"An error occurred while trying to clone the channel: {str(e)}"
        )
        error.set_author(name="Error")
        await ctx.send(embed=error)
        

        




      




  @commands.command(aliases=["deletesticker", "removesticker"], description="Delete the sticker from the server")
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.has_permissions(manage_emojis=True)
  @commands.bot_has_permissions(manage_emojis=True)
  async def delsticker(self, ctx: commands.Context, *, name=None):
        if ctx.message.reference is None:
            return await ctx.reply("No replied message found")
        msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        if len(msg.stickers) == 0:
            return await ctx.reply("No sticker found")
        try:
            name = ""
            for i in msg.stickers:
                name = i.name
                await ctx.guild.delete_sticker(i)
            await ctx.reply(f"{TICK}> Sucessfully deleted sticker named `{name}`")
        except:
            await ctx.reply("Failed to delete the sticker")


  @commands.command(aliases=["deleteemoji", "removeemoji"], description="Deletes the emoji from the server")
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.has_permissions(manage_emojis=True)
  async def delemoji(self, ctx, emoji: str = None):
    init_message = await ctx.reply("Processing to delete emojis...", mention_author=False)
    message_content = None

    
    if ctx.message.reference is not None:
        referenced_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        message_content = str(referenced_message.content)
    else:
        message_content = str(ctx.message.content)

    
    if message_content:
        
        emoji_pattern = r"<a?:\w+:(\d+)>"
        found_emojis = re.findall(emoji_pattern, message_content)
        delete_count = 0

        if len(found_emojis) != 0:
            
            if len(found_emojis) > 15:
                await init_message.delete()
                return await ctx.reply("Maximum 15 emojis can be deleted at a time.")

            
            for emoji_id in found_emojis:
                try:
                    emoji_to_delete = await ctx.guild.fetch_emoji(int(emoji_id))
                    await emoji_to_delete.delete(reason=f"Deleted by {ctx.author}")
                    delete_count += 1
                except discord.NotFound:
                    continue  
                except discord.Forbidden:
                    continue  
            await init_message.delete()
            return await ctx.reply(f"{TICK}> | Successfully deleted {delete_count}/{len(found_emojis)} emoji(s).")

    
    await init_message.delete()
    return await ctx.reply("No valid emoji found to delete.")



  
  @commands.command(description="Changes the icon for the role.")
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.has_permissions(administrator=True)
  @commands.bot_has_guild_permissions(manage_roles=True)
  async def roleicon(self, ctx: commands.Context, role: discord.Role, *, icon: Union[discord.Emoji, discord.PartialEmoji, str] = None):
    
    if role.position >= ctx.guild.me.top_role.position:
        error_embed = discord.Embed(
            description=f"{role.mention} is higher than my role. Please move my role above it.",
            color=self.color
        )
        error_embed.set_author(name="Error")
        error_embed.set_footer(
            text=f"Requested by {ctx.author}",
            icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url
        )
        return await ctx.send(embed=error_embed)

    
    if ctx.author != ctx.guild.owner and ctx.author.top_role.position <= role.position:
        error_embed = discord.Embed(
            description=f"{role.mention} has the same or a higher position than your top role!",
            color=self.color
        )
        error_embed.set_author(name="Error")
        error_embed.set_footer(
            text=f"Requested by {ctx.author}",
            icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url
        )
        return await ctx.send(embed=error_embed)

    
    if icon is None:
        attachment_found = False
        attachment_url = None
        for attachment in ctx.message.attachments:
            attachment_url = attachment.url
            attachment_found = True

        if attachment_found:
            try:
                async with aiohttp.request("GET", attachment_url) as r:
                    image_data = await r.read()
                await role.edit(display_icon=image_data)
                success_embed = discord.Embed(
                    description=f"Successfully changed the icon of {role.mention}.",
                    color=self.color
                )
                success_embed.set_author(name="Icon Updated")
                success_embed.set_footer(
                    text=f"Requested by {ctx.author}",
                    icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url
                )
                return await ctx.send(embed=success_embed)
            except Exception as e:
                print(e)
                return await ctx.reply("Failed to change the icon of the role.")
        else:
            await role.edit(display_icon=None)
            removal_embed = discord.Embed(
                description=f"Successfully removed the icon from {role.mention}.",
                color=self.color
            )
            removal_embed.set_author(name="Icon Removed")
            removal_embed.set_footer(
                text=f"Requested by {ctx.author}",
                icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url
            )
            return await ctx.reply(embed=removal_embed, mention_author=False)

    
    if isinstance(icon, discord.Emoji) or isinstance(icon, discord.PartialEmoji):
        emoji_url = f"https://cdn.discordapp.com/emojis/{icon.id}.png"
        try:
            async with aiohttp.request("GET", emoji_url) as r:
                image_data = await r.read()
            await role.edit(display_icon=image_data)
            success_embed = discord.Embed(
                description=f"Successfully changed the icon for {role.mention} to {icon}.",
                color=self.color
            )
            success_embed.set_author(name="Icon Updated")
            success_embed.set_footer(
                text=f"Requested by {ctx.author}",
                icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url
            )
            return await ctx.reply(embed=success_embed, mention_author=False)
        except Exception as e:
            print(e)
            return await ctx.reply("Failed to change the icon of the role.")

    
    else:
        if not icon.startswith("https://"):
            return await ctx.reply("Please provide a valid link.")
        try:
            async with aiohttp.request("GET", icon) as r:
                image_data = await r.read()
            await role.edit(display_icon=image_data)
            success_embed = discord.Embed(
                description=f"{TICK}>| Successfully changed the icon for {role.mention}.",
                color=self.color
            )
            return await ctx.reply(embed=success_embed, mention_author=False)
        except Exception as e:
            print(e)
            return await ctx.reply("An error occurred while changing the icon for the role.")
  
  
      
  
  @commands.hybrid_command(name="audit",
                           help="See recents audit log action in the server .")
  @blacklist_check()
  @ignore_check()
  @commands.has_permissions(view_audit_log=True)
  @commands.bot_has_permissions(view_audit_log=True)
  @commands.cooldown(1, 5, commands.BucketType.user)
  @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
  @commands.guild_only()
  async def auditlog(self, ctx, limit: int):
    if limit >= 31:
      await ctx.reply(
        "Action rejected, you are not allowed to fetch more than `30` entries.",
        mention_author=False)
      return
    idk = []
    str = ""
    async for entry in ctx.guild.audit_logs(limit=limit):
      idk.append(f'''User: `{entry.user}`
Action: `{entry.action}`
Target: `{entry.target}`
Reason: `{entry.reason}`\n\n''')
    for n in idk:
      str += n
    str = str.replace("AuditLogAction.", "")
    embed = discord.Embed(title=f"Audit Logs Of {ctx.guild.name}",
                          description=f">>> {str}",
                          color=0xFFFFFF)
    embed.set_footer(text=f"Audit Log Actions For {ctx.guild.name}")
    await ctx.reply(embed=embed, mention_author=False)
      
