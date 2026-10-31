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
from utils.emoji import CROSS, TICK, ZWARNING
import discord
from discord.ext import commands, tasks
import asyncio
import datetime
import re
from typing import *
from utils.Tools import *
from discord.ui import Button, View
from typing import Union, Optional
from typing import Union, Optional
from io import BytesIO
import requests
import aiohttp
import time
from datetime import datetime, timezone, timedelta


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


class Role(commands.Cog, name="ZXRole"):

  def __init__(self, bot):
    self.bot = bot
    self.color = 0xFFFFFF


  @commands.group(invoke_without_command=True, name='__zx_role', hidden=True)
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 5, commands.BucketType.user)
  @commands.has_permissions(manage_roles=True)
  @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
  @commands.guild_only()
  @top_check()
  @blacklist_check()
  async def role(self, ctx, member: discord.Member, *, role: discord.Role):
    if not ctx.guild.me.guild_permissions.manage_roles:
        return await ctx.send(f"{ZWARNING} I don't have permission to manage roles!")

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


  @role.command(help="Give role to member for particular time")
  @commands.bot_has_permissions(manage_roles=True)
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 7, commands.BucketType.user)
  @commands.has_permissions(manage_roles=True)
  @commands.bot_has_permissions(manage_roles=True)
  async def temp(self, ctx, role: discord.Role, time, *, user: discord.Member):
    if ctx.author != ctx.guild.owner and role.position >= ctx.author.top_role.position:
        embed = discord.Embed(
              description=f"You can't manage a role that is higher or equal to your top role!",
              color=self.color
          )
        embed.set_author(name="Error")
        embed.set_footer(text=f"Requested by {ctx.author}",
                        icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        return await ctx.send(embed=embed)
          
    else:
      if role.position >= ctx.guild.me.top_role.position:
        embed1 = discord.Embed(
          description=
          f"{role} is higher than my top role, move my role above {role}.",
          color=self.color)
        embed1.set_author(name="Error")
        embed1.set_footer(text=f"Requested by {ctx.author}",
                        icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        return await ctx.send(embed=embed1)
    seconds = convert(time)
    await user.add_roles(role, reason=None)
    success = discord.Embed(
      description=
      f"Successfully added {role.mention} to {user.mention} .",
      color=self.color)
    success.set_author(name="Success")
    success.set_footer(text=f"Requested by {ctx.author}",
                        icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
    await ctx.send(embed=success)
    await asyncio.sleep(seconds)
    await user.remove_roles(role)

  
      









  @role.command(name="unverified", help="Gives role to all the unverified members in the guild")
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 10, commands.BucketType.user)
  @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
  @commands.guild_only()
  @commands.has_permissions(administrator=True)
  async def role_unverified(self, ctx, *, role: discord.Role):
    if ctx.author == ctx.guild.owner or ctx.author.top_role.position > ctx.guild.me.top_role.position:
        button = Button(label="Confirm",
                        style=discord.ButtonStyle.green,
                        emoji=f"{TICK}>")
        button1 = Button(label="Cancel",
                         style=discord.ButtonStyle.red,
                         emoji=CROSS)

        async def button_callback(interaction: discord.Interaction):
            count = 0
            if interaction.user == ctx.author:
                if interaction.guild.me.guild_permissions.manage_roles:
                    embed1 = discord.Embed(
                        color=self.color,
                        description=f"Adding {role.mention} to all unverified members.")
                    await interaction.response.edit_message(embed=embed1, view=None)
                    for member in interaction.guild.members:
                        if member.avatar is None and role not in member.roles:
                            try:
                                await member.add_roles(role, reason=f"Role Unverified Command Executed By: {ctx.author}")
                                count += 1
                            except Exception as e:
                                print(e)

                    await interaction.channel.send(
                        content=f"{TICK}> | Successfully added {role.mention} to {count} unverified member(s).")
                else:
                    await interaction.response.edit_message(
                        content="I am missing the required permission. Please grant the necessary permissions and try again.",
                        embed=None,
                        view=None)
            else:
                await interaction.response.send_message(
                    "This action is not for you!",
                    embed=None,
                    view=None,
                    ephemeral=True)

        async def button1_callback(interaction: discord.Interaction):
            if interaction.user == ctx.author:
                embed2 = discord.Embed(
                    color=self.color,
                    description=f"Action cancelled. No unverified members will be assigned the role {role.mention}.")
                await interaction.response.edit_message(embed=embed2, view=None)
            else:
                await interaction.response.send_message(
                    "This action is not for you!",
                    embed=None,
                    view=None,
                    ephemeral=True)

        embed = discord.Embed(
            color=self.color,
            description=f'**Are you sure you want to give {role.mention} to all unverified members in this guild?**')
        view = View()
        button.callback = button_callback
        button1.callback = button1_callback
        view.add_item(button)
        view.add_item(button1)
        await ctx.reply(embed=embed, view=view, mention_author=False)

    else:
        denied = discord.Embed(title=f"{CROSS} Access Denied",
            description="Your role should be above my top role.",
            color=0xFFFFFF)
        denied.set_footer(text=f"“{ctx.command.qualified_name}” Command executed by {ctx.author}",
                   icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        await ctx.send(embed=denied, mention_author=False)







        



    




    
    


  

 