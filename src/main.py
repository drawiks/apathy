import logging
import sys
from pathlib import Path

import discord
from discord.ext import commands

sys.path.insert(0, str(Path(__file__).parent.parent))

import config

TOKEN = config.TOKEN

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler("app.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.reactions = True
intents.presences = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None
)


@bot.event
async def on_ready():
    logger.info(f"Bot started: {bot.user} (ID: {bot.user.id})")

    bot.role_messages = {}
    extensions = ["cogs.welcome", "cogs.activity", "cogs.basic", "cogs.moderation", "cogs.modlog", "cogs.automod", "cogs.weekly_top"]
    for ext in extensions:
        if ext in bot.extensions:
            await bot.reload_extension(ext)
        else:
            await bot.load_extension(ext)

    try:
        synced = await bot.tree.sync()
        logger.info(f"synced {len(synced)} slash commands globally")
    except Exception as e:
        logger.error(f"failed to sync: {e}")

    logger.info("extensions loaded")


def main():
    if not TOKEN:
        logger.error("BOT_TOKEN not found in .env")
        return

    logger.info("starting")
    bot.run(TOKEN)


if __name__ == "__main__":
    main()