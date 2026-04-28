import logging
import os
from datetime import timedelta
import discord
from discord.ext import commands

from config import WELCOME_CHANNEL, ROLE_CHANNEL, BASE_ROLE, SPAM_LIMIT, SPAM_TIMEOUT_SECONDS, EMBED_COLOR, WELCOME_GIF
from core.checks import is_immune

logger = logging.getLogger(__name__)


class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.message_times = {}

    def _get_modlog(self):
        return self.bot.get_cog("Modlog")

    async def _log_action(self, action: str, member: discord.Member, moderator: discord.Member, reason: str, color: int = EMBED_COLOR):
        modlog = self._get_modlog()
        if modlog:
            await modlog.log_action(member.guild, action, member, moderator, reason, color)

    def _create_welcome_embed(self, member, channel_mention: str = None):
        role = member.guild.get_role(BASE_ROLE)
        role_channel = member.guild.get_channel(ROLE_CHANNEL)

        description = f"ты пока опущенный выбери роль в {role_channel.mention}\nты получил роль {role.mention}"

        embed = discord.Embed(
            title=f"салам {member.name}",
            description=description,
            color=EMBED_COLOR
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"ID: {member.id}")
        if os.path.exists(WELCOME_GIF):
            embed.set_image(url="attachment://welcome.png")
        return embed

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.bot:
            return

        welcome_channel = self.bot.get_channel(WELCOME_CHANNEL)
        if not welcome_channel:
            logger.warning(f"WELCOME_CHANNEL {WELCOME_CHANNEL} not found")
            return

        role = member.guild.get_role(BASE_ROLE)
        if role:
            try:
                await member.add_roles(role)
            except discord.Forbidden:
                pass

        embed = self._create_welcome_embed(member)

        if os.path.exists(WELCOME_GIF):
            file = discord.File(WELCOME_GIF)
            await welcome_channel.send(embed=embed, file=file)
        else:
            await welcome_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if message.guild is None:
            return

        if is_immune(message.author):
            return

        user_id = message.author.id
        current_time = message.created_at.timestamp()

        if user_id not in self.message_times:
            self.message_times[user_id] = []

        self.message_times[user_id] = [
            t for t in self.message_times[user_id]
            if current_time - t < 5
        ]

        self.message_times[user_id].append(current_time)

        if len(self.message_times[user_id]) > SPAM_LIMIT:
            self.message_times[user_id] = []

            try:
                await message.author.timeout(
                    discord.utils.utcnow() +
                    timedelta(seconds=SPAM_TIMEOUT_SECONDS),
                    reason="спам детект"
                )
                await self._log_action(
                    f"таймаут ({SPAM_TIMEOUT_SECONDS // 60} мин)",
                    message.author,
                    message.author,
                    "спам детект",
                    0xFF0000
                )
            except discord.Forbidden:
                pass

            embed = discord.Embed(
                title="анти-спам",
                description=f"{message.author.mention} получил таймаут за спам "
                             f"({SPAM_TIMEOUT_SECONDS // 60} минут)",
                color=EMBED_COLOR
            )
            await message.channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Welcome(bot))