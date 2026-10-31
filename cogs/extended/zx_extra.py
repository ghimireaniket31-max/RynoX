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

import os 
import discord
from utils.emoji import BOOST, CODEBASE, CROSS, KING, TICK, UPTIME, ZWARNING
from discord.ext import commands
import datetime
import sys
from discord.ui import Button, View, LayoutView, TextDisplay, Separator, Container, ActionRow, MediaGallery
from utils.cv2 import CV2, build_container
import psutil
import time
from utils.Tools import *
from discord.ext import commands, menus
from discord.ext.commands import BucketType, cooldown
import requests
from typing import *
from utils import *
from utils.config import BotName, serverLink
from utils import Paginator, DescriptionEmbedPaginator, FieldPagePaginator, TextPaginator
from core import Cog, zyrox, Context
from typing import Optional
import aiosqlite 
import asyncio
import aiohttp


start_time = time.time()


def datetime_to_seconds(thing: datetime.datetime):
  current_time = datetime.datetime.fromtimestamp(time.time())
  return round(
    round(time.time()) +
    (current_time - thing.replace(tzinfo=None)).total_seconds())

tick = f"{TICK}>"
cross = CROSS




class RoleInfoView(View):
  def __init__(self, role: discord.Role, author_id):
    super().__init__(timeout=180)
    self.role = role
    self.author_id = author_id

  @discord.ui.button(label='Show Permissions',  emoji=f"{CODEBASE} ", style=discord.ButtonStyle.secondary)
  async def show_permissions(self, interaction: discord.Interaction, button: Button):
    if interaction.user.id != self.author_id:
          await interaction.response.send_message("Uh oh! That message doesn't belong to you. You must run this command to interact with it.", ephemeral=True)
          return

    permissions = [perm.replace("_", " ").title() for perm, value in self.role.permissions if value]
    permission_text = ", ".join(permissions) if permissions else "None"
    await interaction.response.send_message(view=CV2(f"Permissions for {self.role.name}", permission_text or "No permissions."), ephemeral=True)

    
class OverwritesView(View):
  def __init__(self, channel, author_id):
      super().__init__(timeout=180)
      self.channel = channel
      self.author_id = author_id

  @discord.ui.button(label='Show Overwrites', style=discord.ButtonStyle.primary)
  async def show_overwrites(self, interaction: discord.Interaction, button: Button):
      if interaction.user.id != self.author_id:
          await interaction.response.send_message("Uh oh! That message doesn't belong to you. You must run this command to interact with it.", ephemeral=True)
          return

      overwrites = []
      for target, perms in self.channel.overwrites.items():
          permissions = {
              "View Channel": perms.view_channel,
              "Send Messages": perms.send_messages,
              "Read Message History": perms.read_message_history,
              "Manage Messages": perms.manage_messages,
              "Embed Links": perms.embed_links,
              "Attach Files": perms.attach_files,
              "Manage Channels": perms.manage_channels,
              "Manage Permissions": perms.manage_permissions,
              "Manage Webhooks": perms.manage_webhooks,
              "Create Instant Invite": perms.create_instant_invite,
              "Add Reactions": perms.add_reactions,
              "Mention Everyone": perms.mention_everyone,
              "Kick Members": perms.kick_members,
              "Ban Members": perms.ban_members,
              "Moderate Members": perms.moderate_members,
              "Send TTS Messages": perms.send_tts_messages,
              "Use External Emojis": perms.external_emojis,
              "Use External Stickers": perms.external_stickers,
              "View Audit Log": perms.view_audit_log,
              "Voice Mute Members": perms.mute_members,
              "Voice Deafen Members": perms.deafen_members,
              "Administrator": perms.administrator
          }

          overwrites.append(f"**For {target.name}**\n" +
                            "\n".join(f"  * **{perm}:** {'{TICK}>' if value else '{CROSS}' if value is False else '⛔'}" for perm, value in permissions.items()))

      ow_text = "\n".join(overwrites) if overwrites else "No overwrites for this channel."
      footer = f"{TICK}> = Allowed, {CROSS} = Denied, ⛔ = None"
      await interaction.response.send_message(view=CV2(f"Overwrites for {self.channel.name}", ow_text, footer), ephemeral=True)




class Extra(commands.Cog):

  def __init__(self, bot):
    self.bot = bot
    self.color = 0xFFFFFF
    self.start_time = datetime.datetime.now()



  


  
  


    

        

  


























  @commands.command(name="joined-at",
                    help="Shows when a user joined",
                    usage="joined-at [user]",
                    with_app_command=True)
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  async def joined_at(self, ctx):
    joined = ctx.author.joined_at.strftime("%a, %d %b %Y %I:%M %p")
    await ctx.send(view=CV2("joined-at", f"**`{joined}`**"))

  @commands.command(name="github", usage="github [search]")
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  async def github(self, ctx, *, search_query):
    json = requests.get(
      f"https://api.github.com/search/repositories?q={search_query}").json()

    if json["total_count"] == 0:
      await ctx.send(f"No matching repositories found with the name: {search_query}")
    else:
      await ctx.send(
        f"Found result for '{search_query}':\n{json['items'][0]['html_url']}")

  @commands.hybrid_command(name="vcinfo",
                           description="View information about a voice channel.",
                           help="View information about a voice channel.", 
                           usage="<VoiceChannel>",
                           with_app_command=True)
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  async def vcinfo(self, ctx, channel: discord.VoiceChannel = None):
    if channel is None:
      await ctx.reply(view=CV2(f"{cross} Error", "Please provide a valid voice channel."))
      return
    vc_text = (
        f"**ID:** {channel.id}\n**Members:** {len(channel.members)}\n"
        f"**Bitrate:** {channel.bitrate/1000} kbps\n"
        f"**Created At:** {channel.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"**Category:** {channel.category.name if channel.category else 'None'}\n"
        f"**Region:** {channel.rtc_region}"
    )
    if channel.user_limit:
        vc_text += f"\n**User Limit:** {channel.user_limit}"
    view = LayoutView(timeout=None)
    join_btn = Button(label="Join", style=discord.ButtonStyle.link, url=f"https://discord.com/channels/{ctx.guild.id}/{channel.id}")
    view.add_item(build_container(
        TextDisplay(f"**Voice Channel Info — {channel.name}**"),
        Separator(visible=True),
        TextDisplay(vc_text),
        ActionRow(join_btn)
    ))
    await ctx.send(view=view)








  
  @commands.command(name="permissions", aliases= ["perms"],
                           help="Check and list the key permissions of a specific user",
                           usage="perms <user>",
                           with_app_command=True)
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  async def keyperms(self, ctx, member: discord.Member):
    key_permissions = []

    if member.guild_permissions.create_instant_invite:
      key_permissions.append("Create Instant Invite")
    if member.guild_permissions.kick_members:
      key_permissions.append("Kick Members")
    if member.guild_permissions.ban_members:
      key_permissions.append("Ban Members")
    if member.guild_permissions.administrator:
      key_permissions.append("Administrator")
    if member.guild_permissions.manage_channels:
      key_permissions.append("Manage Channels")
    if member.guild_permissions.manage_messages:
      key_permissions.append("Manage Messages")
    if member.guild_permissions.mention_everyone:
      key_permissions.append("Mention Everyone")
    if member.guild_permissions.manage_nicknames:
      key_permissions.append("Manage Nicknames")
    if member.guild_permissions.manage_roles:
      key_permissions.append("Manage Roles")
    if member.guild_permissions.manage_webhooks:
      key_permissions.append("Manage Webhooks")
    if member.guild_permissions.manage_emojis:
      key_permissions.append("Manage Emojis")
    if member.guild_permissions.manage_guild:
      key_permissions.append("Manage Server")
    if member.guild_permissions.manage_permissions:
      key_permissions.append("Manage Permissions")
    if member.guild_permissions.manage_threads:
      key_permissions.append("Manage Threads")
    if member.guild_permissions.moderate_members:
      key_permissions.append("Moderate Members")
    if member.guild_permissions.move_members:
      key_permissions.append("Move Members")
    if member.guild_permissions.mute_members:
      key_permissions.append("Mute Members (VC)")
    if member.guild_permissions.deafen_members:
      key_permissions.append("Deafen Members")
    if member.guild_permissions.priority_speaker:
      key_permissions.append("Priority Speaker")
    if member.guild_permissions.stream:
      key_permissions.append("Stream")
    
    
    

    permissions_list = ", ".join(key_permissions) if key_permissions else "None"

    await ctx.reply(view=CV2(f"Key Permissions of {member}", f"__**Key Permissions**__\n{permissions_list}"))

  




  @commands.hybrid_command(name="report",
                           aliases=["bug"],
                           usage='Report <bug>',
                           description='Report a bug to the Development team.',
                           help='Report a bug to the Development team.',
                           with_app_command=True)
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 30, commands.BucketType.channel)
  async def report(self, ctx, *, bug):
    try:
      channel = self.bot.get_channel(int(os.getenv("REPORT_CHANNEL_ID", "0")))
    except ValueError:
      channel = None
    if channel is None:
      return await ctx.reply(view=CV2(f"{CROSS} Reports unavailable", "Bug reports are not configured. Set REPORT_CHANNEL_ID in the .env file."))
    report_text = f"{bug}\n\n**Reported By:** {ctx.author.name}\n**Server:** {ctx.guild.name}\n**Channel:** {ctx.channel.name}"
    await channel.send(view=CV2("Bug Reported", report_text))
    await ctx.reply(view=CV2(f"{TICK} Bug Reported", "Thank you for reporting the bug. We will look into it."))

