
import discord
from discord.ext import commands


class Mention(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):

        if message.author.bot:
            return

        if not self.bot.user:
            return

        # Respond only to a direct bot mention
        if self.bot.user in message.mentions:
            embed = discord.Embed(
                title="RynoX",
                description=(
                    f"Hello {message.author.mention}!\n\n"
                    "I'm **RynoX**, your multipurpose Discord bot.\n\n"
                    f"**Prefix:** `{'.'}`\n"
                    "**Need help?** Use `.help` to explore my commands."
                ),
                color=discord.Color.dark_grey()
            )

            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
            embed.set_footer(text="RynoX • Advanced Discord Management")

            await message.reply(
                embed=embed,
                mention_author=False
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Mention(bot))
