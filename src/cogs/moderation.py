import asyncio
from datetime import timedelta

import discord
from discord import app_commands
from discord.ext import commands

from config import EMBED_COLOR
from utils.checks import is_moderator
from utils.database import add_warning, get_warnings, remove_warnings


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="kick", description="кик участника")
    async def kick(self, interaction: discord.Interaction, member: discord.Member, *, reason: str = "не указана"):
        if not is_moderator(interaction.user):
            await interaction.response.send_message("нет прав", ephemeral=True)
            return

        if member == interaction.user:
            await interaction.response.send_message("нельзя кикнуть самого себя", ephemeral=True)
            return

        if member.top_role >= interaction.user.top_role:
            await interaction.response.send_message("ты не можешь кикнуть этого пользователя", ephemeral=True)
            return

        await member.kick(reason=reason)

        embed = discord.Embed(
            title="кик",
            description=f"{member} был кикнут.\nпричина: {reason}",
            color=EMBED_COLOR
        )
        embed.set_footer(text=f"модератор: {interaction.user}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ban", description="забанить участника")
    async def ban(self, interaction: discord.Interaction, member: discord.Member, *, reason: str = "не указана"):
        if not is_moderator(interaction.user):
            await interaction.response.send_message("нет прав", ephemeral=True)
            return

        if member == interaction.user:
            await interaction.response.send_message("нельзя забанить самого себя", ephemeral=True)
            return

        if member.top_role >= interaction.user.top_role:
            await interaction.response.send_message("ты не можешь забанить этого пользователя", ephemeral=True)
            return

        await member.ban(reason=reason, delete_message_days=0)

        embed = discord.Embed(
            title="бан",
            description=f"{member} был забанен.\nпричина: {reason}",
            color=EMBED_COLOR
        )
        embed.set_footer(text=f"модератор: {interaction.user}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="unban", description="разбанить участника")
    async def unban(self, interaction: discord.Interaction, user: discord.User, *, reason: str = "не указана"):
        if not is_moderator(interaction.user):
            await interaction.response.send_message("нет прав", ephemeral=True)
            return

        try:
            await interaction.guild.unban(user, reason=reason)
        except discord.NotFound:
            await interaction.response.send_message("пользователь не в бане", ephemeral=True)
            return

        embed = discord.Embed(
            title="разбан",
            description=f"{user} был разбанен.",
            color=EMBED_COLOR
        )
        embed.set_footer(text=f"Модератор: {interaction.user}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="mute", description="мут участника")
    async def mute(self, interaction: discord.Interaction, member: discord.Member, duration: int = 60, *, reason: str = "не указана"):
        if not is_moderator(interaction.user):
            await interaction.response.send_message("нет прав", ephemeral=True)
            return

        if member.id == interaction.user.id:
            await interaction.response.send_message("нельзя замутить самого себя", ephemeral=True)
            return

        timeout_duration = timedelta(minutes=duration)

        try:
            await member.timeout(discord.utils.utcnow() + timeout_duration, reason=reason)
        except discord.Forbidden:
            await interaction.response.send_message("недостаточно прав", ephemeral=True)
            return

        embed = discord.Embed(
            title="мут",
            description=f"{member} получил мут на {duration} минут.\nпричина: {reason}",
            color=EMBED_COLOR
        )
        embed.set_footer(text=f"модератор: {interaction.user}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="unmute", description="размутить участника")
    async def unmute(self, interaction: discord.Interaction, member: discord.Member):
        if not is_moderator(interaction.user):
            await interaction.response.send_message("нет прав", ephemeral=True)
            return

        try:
            await member.timeout(None)
        except discord.Forbidden:
            await interaction.response.send_message("недостаточно прав", ephemeral=True)
            return

        embed = discord.Embed(
            title="размут",
            description=f"{member} был размучен.",
            color=EMBED_COLOR
        )
        embed.set_footer(text=f"модератор: {interaction.user}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="clear", description="очистить сообщения")
    async def clear(self, interaction: discord.Interaction, amount: int):
        if not is_moderator(interaction.user):
            await interaction.response.send_message("нет прав", ephemeral=True)
            return

        if amount < 1 or amount > 1000:
            await interaction.response.send_message("количество должно быть от 1 до 1000", ephemeral=True)
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
            title="фистинг",
            description=f"удалено {deleted} сообщений.",
            color=EMBED_COLOR
        )
        embed.set_footer(text=f"модератор: {interaction.user}")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="warn", description="выдать предупреждение")
    async def warn(self, interaction: discord.Interaction, member: discord.Member, *, reason: str):
        if not is_moderator(interaction.user):
            await interaction.response.send_message("нет прав", ephemeral=True)
            return

        add_warning(member.id, interaction.guild.id, reason, interaction.user.id)

        warnings = get_warnings(member.id, interaction.guild.id)
        warn_count = len(warnings)

        embed = discord.Embed(
            title="предупреждение",
            description=f"{member} получил предупреждение.\n"
                        f"причина: {reason}\n"
                        f"всего предупреждений: {warn_count}",
            color=EMBED_COLOR
        )
        embed.set_footer(text=f"модератор: {interaction.user}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="warnings", description="показать предупреждения")
    async def warnings(self, interaction: discord.Interaction, member: discord.Member):
        if not is_moderator(interaction.user):
            await interaction.response.send_message("нет прав", ephemeral=True)
            return

        warnings = get_warnings(member.id, interaction.guild.id)

        if not warnings:
            await interaction.response.send_message(f"у {member} нет предупреждений.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"предупреждения {member}",
            color=EMBED_COLOR
        )

        for i, w in enumerate(warnings, 1):
            embed.add_field(
                name=f"#{i}",
                value=w.get("reason", "без причины"),
                inline=False
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="unwarn", description="снять все предупреждения")
    async def unwarn(self, interaction: discord.Interaction, member: discord.Member):
        if not is_moderator(interaction.user):
            await interaction.response.send_message("нет прав", ephemeral=True)
            return

        remove_warnings(member.id, interaction.guild.id)

        embed = discord.Embed(
            title="предупреждения сняты",
            description=f"все предупреждения {member} были сняты.",
            color=EMBED_COLOR
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Moderation(bot))