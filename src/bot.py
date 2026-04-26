import logging
import sys
from pathlib import Path
from typing import Any

import discord
from discord.ext import commands

import config


class ApathyBot(commands.Bot):
    def __init__(self) -> None:
        self.logger = self._setup_logging()
        
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        intents.reactions = True
        intents.presences = True
        intents.voice_states = True
        
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None
        )
        
        self._register_events()
    
    def _setup_logging(self) -> logging.Logger:
        logger = logging.getLogger("apathy")
        logger.setLevel(logging.DEBUG)
        
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )
        
        file_handler = logging.FileHandler(
            "app.log", encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _register_events(self) -> None:
        self.on_command_error = self._handle_command_error
    
    async def _handle_command_error(
        self, 
        ctx: commands.Context, 
        error: commands.CommandError
    ) -> None:
        match error:
            case commands.CommandNotFound():
                await ctx.send("команда не найдена.")
            case commands.MissingRequiredArgument() as e:
                await ctx.send(
                    f"отсутствует обязательный аргумент: `{e.param.name}`"
                )
            case commands.MemberNotFound() as e:
                await ctx.send(f"участник `{e.argument}` не найден.")
            case commands.BadArgument() as e:
                await ctx.send(f"неверный аргумент: {e}")
            case commands.CommandOnCooldown() as e:
                await ctx.send(
                    f"команда на кулдауне. попробуй через {e.retry_after:.1f} сек."
                )
            case commands.CheckFailure():
                await ctx.send("у тебя нет прав на эту команду.")
            case commands.NotOwner():
                await ctx.send("у тебя нет прав на эту команду.")
            case _:
                self.logger.exception(
                    f"Unhandled error in {ctx.command}: {error}"
                )
                await ctx.send("произошла ошибка при выполнении команды.")
    
    async def load_cogs(self) -> None:
        cogs_dir = Path(__file__).parent / "cogs"
        
        for cog_file in cogs_dir.glob("*.py"):
            if cog_file.stem == "__init__":
                continue
            cog_package = f"cogs.{cog_file.stem}"
            
            if cog_package in self.extensions:
                await self.reload_extension(cog_package)
            else:
                await self.load_extension(cog_package)
        
        self.logger.info(f"loaded {len(self.extensions)} cogs")
    
    async def on_ready(self) -> None:
        self.logger.info(f"Bot started: {self.user} (ID: {self.user.id})")
        await self.load_cogs()
        
        try:
            synced = await self.tree.sync()
            self.logger.info(f"synced {len(synced)} slash commands")
        except Exception as e:
            self.logger.error(f"failed to sync: {e}")
    
    async def on_error(self, event: str, *args: Any, **kwargs: Any) -> None:
        exc_info = sys.exc_info()
        self.logger.error(f"Unhandled error in {event}: {exc_info[1]}")
    
    async def on_rate_limit(self, error: Any) -> None:
        self.logger.warning(f"Rate limited: {error}")