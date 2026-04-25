import logging
import discord
from discord.ext import commands

from config import MODLOG_CHANNEL, EMBED_COLOR

logger = logging.getLogger(__name__)


class Modlog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _send_log(self, guild, embed):
        channel = guild.get_channel(MODLOG_CHANNEL)
        if channel:
            try:
                await channel.send(embed=embed)
            except Exception as e:
                logger.error(f"Failed to send modlog: {e}")

    async def log_action(
        self,
        guild,
        action: str,
        member: discord.Member,
        moderator: discord.Member = None,
        reason: str = None,
        color: int = EMBED_COLOR
    ):
        description = f"**участник:** {member.mention} ({member.name})\n"
        if moderator:
            description += f"**модератор:** {moderator.mention}\n"
        if reason:
            description += f"**причина:** {reason}"

        embed = discord.Embed(
            title=action,
            description=description,
            color=color
        )
        await self._send_log(guild, embed)

    async def log_message_delete(self, message: discord.Message, reason: str):
        embed = discord.Embed(
            title="сообщение удалено",
            description=f"**автор:** {message.author.mention}\n"
                        f"**канал:** {message.channel.mention}\n"
                        f"**причина:** {reason}",
            color=0xFF0000
        )
        if message.content:
            embed.add_field(name="содержание", value=message.content[:500], inline=False)
        await self._send_log(message.guild, embed)

    async def log_member_leave(self, member: discord.Member):
        embed = discord.Embed(
            title="участник покинул сервер",
            description=f"**участник:** {member.mention} ({member.name})",
            color=0xFFA500
        )
        await self._send_log(member.guild, embed)

    async def log_member_join(self, member: discord.Member):
        embed = discord.Embed(
            title="участник присоединился",
            description=f"**участник:** {member.mention} ({member.name})",
            color=0x00FF00
        )
        await self._send_log(member.guild, embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if member.bot:
            return
        await self.log_member_leave(member)


async def setup(bot):
    await bot.add_cog(Modlog(bot))