import asyncio
import logging
import sys
from datetime import timedelta
from pathlib import Path

import discord
from discord.ext import commands

sys.path.insert(0, str(Path(__file__).parent.parent))

import config
from config import EMBED_COLOR, BASE_ROLE, ROLE_CHANNEL
from utils.checks import is_moderator
from utils.database import add_warning, get_warnings, remove_warnings

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

ROLE_POSITIONS = {
    "1️⃣": 1424326184585531543,
    "2️⃣": 1424326316945309696,
    "3️⃣": 1424326347676975206,
    "4️⃣": 1424326409970516070,
    "5️⃣": 1424326450651336714,
}


@bot.tree.command(name="ping", description="Проверить задержку бота")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    embed = discord.Embed(
        title="Pong!",
        description=f"Задержка: {latency}мс",
        color=EMBED_COLOR
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="команды", description="Список команд бота")
async def commands_list(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Список команд",
        color=EMBED_COLOR
    )

    embed.add_field(
        name="Основные",
        value="/ping - Проверить задержку\n/команды - Этот список",
        inline=False
    )

    if is_moderator(interaction.user):
        embed.add_field(
            name="Модерация",
            value="/kick <участник> [причина]\n"
                  "/ban <участник> [причина]\n"
                  "/unban <участник>\n"
                  "/mute <участник> <минуты> [причина]\n"
                  "/unmute <участник>\n"
                  "/clear <кол-во>\n"
                  "/warn <участник> <причина>\n"
                  "/warnings <участник>\n"
                  "/unwarn <участник>\n"
                  "/roles",
            inline=False
        )

    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="салам", description="Дебаг: показать приветственное сообщение")
async def salam(interaction: discord.Interaction):
    role = interaction.guild.get_role(BASE_ROLE)
    role_channel = interaction.guild.get_channel(ROLE_CHANNEL)

    embed = discord.Embed(
        title=f"салам {interaction.user.name}",
        description=f"ты пока опущенный выбери роль в {role_channel.mention}\nты получил роль {role.mention}",
        color=EMBED_COLOR
    )
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    embed.set_footer(text=f"ID: {interaction.user.id}")
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="kick", description="Кикнуть участника")
async def kick(interaction: discord.Interaction, member: discord.Member, *, reason: str = "Не указана"):
    if not is_moderator(interaction.user):
        await interaction.response.send_message("У вас нет прав!", ephemeral=True)
        return

    if member == interaction.user:
        await interaction.response.send_message("Нельзя кикнуть самого себя!", ephemeral=True)
        return

    if member.top_role >= interaction.user.top_role:
        await interaction.response.send_message("Вы не можете кикнуть этого пользователя!", ephemeral=True)
        return

    await member.kick(reason=reason)

    embed = discord.Embed(
        title="Кик",
        description=f"{member} был кикнут.\nПричина: {reason}",
        color=EMBED_COLOR
    )
    embed.set_footer(text=f"Модератор: {interaction.user}")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="ban", description="Забанить участника")
async def ban(interaction: discord.Interaction, member: discord.Member, *, reason: str = "Не указана"):
    if not is_moderator(interaction.user):
        await interaction.response.send_message("У вас нет прав!", ephemeral=True)
        return

    if member == interaction.user:
        await interaction.response.send_message("Нельзя забанить самого себя!", ephemeral=True)
        return

    if member.top_role >= interaction.user.top_role:
        await interaction.response.send_message("Вы не можете забанить этого пользователя!", ephemeral=True)
        return

    await member.ban(reason=reason, delete_message_days=0)

    embed = discord.Embed(
        title="Бан",
        description=f"{member} был забанен.\nПричина: {reason}",
        color=EMBED_COLOR
    )
    embed.set_footer(text=f"Модератор: {interaction.user}")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="unban", description="Разбанить участника")
async def unban(interaction: discord.Interaction, user: discord.User, *, reason: str = "Не указана"):
    if not is_moderator(interaction.user):
        await interaction.response.send_message("У вас нет прав!", ephemeral=True)
        return

    try:
        await interaction.guild.unban(user, reason=reason)
    except discord.NotFound:
        await interaction.response.send_message("Пользователь не забанен!", ephemeral=True)
        return

    embed = discord.Embed(
        title="Разбан",
        description=f"{user} был разбанен.",
        color=EMBED_COLOR
    )
    embed.set_footer(text=f"Модератор: {interaction.user}")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="mute", description="Замутить участника")
async def mute(interaction: discord.Interaction, member: discord.Member, duration: int = 60, *, reason: str = "Не указана"):
    if not is_moderator(interaction.user):
        await interaction.response.send_message("У вас нет прав!", ephemeral=True)
        return

    if member.id == interaction.user.id:
        await interaction.response.send_message("Нельзя замутить самого себя!", ephemeral=True)
        return

    timeout_duration = timedelta(minutes=duration)

    try:
        await member.timeout(discord.utils.utcnow() + timeout_duration, reason=reason)
    except discord.Forbidden:
        await interaction.response.send_message("Недостаточно прав!", ephemeral=True)
        return

    embed = discord.Embed(
        title="Мут",
        description=f"{member} получил мут на {duration} минут.\nПричина: {reason}",
        color=EMBED_COLOR
    )
    embed.set_footer(text=f"Модератор: {interaction.user}")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="unmute", description="Размутить участника")
async def unmute(interaction: discord.Interaction, member: discord.Member):
    if not is_moderator(interaction.user):
        await interaction.response.send_message("У вас нет прав!", ephemeral=True)
        return

    try:
        await member.timeout(None)
    except discord.Forbidden:
        await interaction.response.send_message("Недостаточно прав!", ephemeral=True)
        return

    embed = discord.Embed(
        title="Размут",
        description=f"{member} был размучен.",
        color=EMBED_COLOR
    )
    embed.set_footer(text=f"Модератор: {interaction.user}")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="clear", description="Очистить сообщения")
async def clear(interaction: discord.Interaction, amount: int):
    if not is_moderator(interaction.user):
        await interaction.response.send_message("У вас нет прав!", ephemeral=True)
        return

    if amount < 1 or amount > 1000:
        await interaction.response.send_message("Количество должно быть от 1 до 1000!", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    deleted = 0
    while amount > 0:
        batch = min(amount, 100)
        messages = await interaction.channel.purge(limit=batch)
        deleted += len(messages)
        amount -= batch
        if amount > 0:
            await asyncio.sleep(1)

    embed = discord.Embed(
        title="Очистка",
        description=f"Удалено {deleted} сообщений.",
        color=EMBED_COLOR
    )
    embed.set_footer(text=f"Модератор: {interaction.user}")
    await interaction.followup.send(embed=embed, ephemeral=True)


@bot.tree.command(name="warn", description="Выдать предупреждение")
async def warn(interaction: discord.Interaction, member: discord.Member, *, reason: str):
    if not is_moderator(interaction.user):
        await interaction.response.send_message("У вас нет прав!", ephemeral=True)
        return

    add_warning(member.id, interaction.guild.id, reason, interaction.user.id)

    warnings = get_warnings(member.id, interaction.guild.id)
    warn_count = len(warnings)

    embed = discord.Embed(
        title="Предупреждение",
        description=f"{member} получил предупреждение.\n"
                     f"Причина: {reason}\n"
                     f"Всего предупреждений: {warn_count}",
        color=EMBED_COLOR
    )
    embed.set_footer(text=f"Модератор: {interaction.user}")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="warnings", description="Показать предупреждения")
async def warnings(interaction: discord.Interaction, member: discord.Member):
    if not is_moderator(interaction.user):
        await interaction.response.send_message("У вас нет прав!", ephemeral=True)
        return

    warnings = get_warnings(member.id, interaction.guild.id)

    if not warnings:
        await interaction.response.send_message(f"У {member} нет предупреждений.", ephemeral=True)
        return

    embed = discord.Embed(
        title=f"Предупреждения {member}",
        color=EMBED_COLOR
    )

    for i, w in enumerate(warnings, 1):
        embed.add_field(
            name=f"#{i}",
            value=w.get("reason", "Без причины"),
            inline=False
        )

    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="unwarn", description="Снять все предупреждения")
async def unwarn(interaction: discord.Interaction, member: discord.Member):
    if not is_moderator(interaction.user):
        await interaction.response.send_message("У вас нет прав!", ephemeral=True)
        return

    remove_warnings(member.id, interaction.guild.id)

    embed = discord.Embed(
        title="Предупреждения сняты",
        description=f"Все предупреждения {member} были сняты.",
        color=EMBED_COLOR
    )
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="roles", description="Отправить сообщение для выбора ролей")
async def roles(interaction: discord.Interaction):
    if not is_moderator(interaction.user):
        await interaction.response.send_message("У вас нет прав!", ephemeral=True)
        return

    embed = discord.Embed(
        title="выбери позицию (можно несколько)",
        description="нажми на эмодзи для получения роли",
        color=EMBED_COLOR
    )

    await interaction.response.send_message(embed=embed)
    msg = await interaction.original_response()

    for emoji in ROLE_POSITIONS.keys():
        await msg.add_reaction(emoji)

    if interaction.guild.id not in bot.role_messages:
        bot.role_messages[interaction.guild.id] = {}
    bot.role_messages[interaction.guild.id][msg.id] = ROLE_POSITIONS


@bot.event
async def on_ready():
    logger.info(f"Bot started: {bot.user} (ID: {bot.user.id})")

    bot.role_messages = {}
    await bot.load_extension("cogs.welcome")
    await bot.load_extension("commands.moderation")
    await bot.load_extension("cogs.activity")

    try:
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} slash commands globally")
    except Exception as e:
        logger.error(f"Failed to sync: {e}")

    logger.info("Extensions loaded")


def main():
    if not TOKEN:
        logger.error("BOT_TOKEN not found in .env")
        return

    logger.info("Starting bot...")
    bot.run(TOKEN)


if __name__ == "__main__":
    main()
