import logging
import sys
import traceback
from pathlib import Path
from glob import glob

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
intents.voice_states = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None
)


async def command_error_handler(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("команда не найдена.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"отсутствует обязательный аргумент: `{error.param.name}`")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send(f"участник `{error.argument}` не найден.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f"неверный аргумент: {error}")
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"команда на кулдауне. попробуй через {error.retry_after:.1f} сек.")
    elif isinstance(error, commands.CheckFailure):
        await ctx.send("у тебя нет прав на эту команду.")
    elif isinstance(error, commands.NotOwner):
        await ctx.send("у тебя нет прав на эту команду.")
    else:
        logger.exception(f"Unhandled command error in {ctx.command}: {error}")
        await ctx.send("произошла ошибка при выполнении команды.")


bot.on_command_error = command_error_handler


@bot.event
async def on_ready():
    logger.info(f"Bot started: {bot.user} (ID: {bot.user.id})")

    bot.role_messages = {}
    cogs_dir = Path(__file__).parent / "cogs"
    for cog_file in cogs_dir.glob("*.py"):
        if cog_file.stem == "__init__":
            continue
        ext = f"cogs.{cog_file.stem}"
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


@bot.event
async def on_error(event, *args, **kwargs):
    exc_info = sys.exc_info()
    logger.error(f"Unhandled error in {event}: {exc_info[1]}", exc_info=exc_info)


@bot.event
async def on_rate_limit(error):
    logger.warning(f"Rate limited: {error}")


def main():
    if not TOKEN:
        logger.error("BOT_TOKEN not found in .env")
        return

    logger.info("starting")
    bot.run(TOKEN)


if __name__ == "__main__":
    main()