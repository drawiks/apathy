import re
import logging

import discord
from discord.ext import commands

from config import AUTO_MOD_ENABLED, FLOOD_CHANNEL, GIF_DOMAINS, EMBED_COLOR
from utils.checks import is_moderator

logger = logging.getLogger(__name__)


class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _extract_urls(self, text: str):
        url_pattern = r'https?://[^\s]+'
        return re.findall(url_pattern, text)

    def _is_gif_url(self, url: str) -> bool:
        url_lower = url.lower()
        for domain in GIF_DOMAINS:
            if domain in url_lower:
                return True
        return False

    def _is_too_much_caps(self, text: str) -> bool:
        if len(text) < 10:
            return False
        letters = [c for c in text if c.isalpha()]
        if not letters:
            return False
        upper = sum(1 for c in letters if c.isupper())
        return (upper / len(letters)) > 0.7

    @commands.Cog.listener()
    async def on_message(self, message):
        if not AUTO_MOD_ENABLED:
            return
        if message.author.bot:
            return
        if message.guild is None:
            return
        if message.channel.id == FLOOD_CHANNEL:
            return
        if is_moderator(message.author):
            return

        content = message.content

        urls = self._extract_urls(content)
        for url in urls:
            if not self._is_gif_url(url):
                try:
                    await message.delete()
                    logger.info(f"Deleted message with link from {message.author}")
                except Exception as e:
                    logger.error(f"Failed to delete message: {e}")
                return

        if "@everyone" in content or "@here" in content:
            try:
                await message.delete()
                logger.info(f"Deleted message with @everyone/@here from {message.author}")
            except Exception as e:
                logger.error(f"Failed to delete message: {e}")
            return

        if self._is_too_much_caps(content):
            try:
                await message.delete()
                logger.info(f"Deleted message with too much caps from {message.author}")
            except Exception as e:
                logger.error(f"Failed to delete message: {e}")
            return


async def setup(bot):
    await bot.add_cog(AutoMod(bot))