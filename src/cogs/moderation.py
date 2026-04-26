import asyncio
from datetime import timedelta

import discord
from discord import app_commands
from discord.ext import commands

from config import EMBED_COLOR
from core.checks import is_moderator
from core.embeds import mod_action_embed
from repos import warning


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _get_modlog(self):
        return self.bot.get_cog("Modlog")

    async def _log_action(self, action: str, member: discord.Member, moderator: discord.Member, reason: str, color: int = EMBED_COLOR):
        modlog = self._get_modlog()
        if modlog:
            await modlog.log_action(member.guild, action, member, moderator, reason, color)

    @app_commands.command(name="kick", description="кик участника")
    async def kick(self, interaction: discord.Interaction, member: discord.Member, *, reason: str = "не указана"):
        if not is_moderator(interaction.user):
            await interaction.response.send_message("нет прав", ephemeral=True)
            return

        if member.bot:
            await interaction.response.send_message("нельзя кикнуть бота", ephemeral=True)
            return

        if member == interaction.user:
            await interaction.response.send_message("нельзя кикнуть самого себя", ephemeral=True)
            return

        if member.top_role >= interaction.user.top_role:
            await interaction.response.send_message("ты не можешь кикнуть этого пользователя", ephemeral=True)
            return

        await member.kick(reason=reason)
        await self._log_action("кик", member, interaction.user, reason, 0xFFA500)

        embed = mod_action_embed("кик", member, interaction.user, reason)
        embed.set_footer(text=f"модератор: {interaction.user}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ban", description="забанить участника")
    async def ban(self, interaction: discord.Interaction, member: discord.Member, *, reason: str = "не указана"):
        if not is_moderator(interaction.user):
            await interaction.response.send_message("нет прав", ephemeral=True)
            return

        if member.bot:
            await interaction.response.send_message("нельзя забанить бота", ephemeral=True)
            return

        if member == interaction.user:
            await interaction.response.send_message("нельзя забанить самого себя", ephemeral=True)
            return

        if member.top_role >= interaction.user.top_role:
            await interaction.response.send_message("ты не можешь забанить этого пользователя", ephemeral=True)
            return

        await member.ban(reason=reason, delete_message_days=0)
        await self._log_action("бан", member, interaction.user, reason, 0xFF0000)

        embed = mod_action_embed("бан", member, interaction.user, reason, color=0xFF0000)
        embed.set_footer(text=f"модератор: {interaction.user}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="unban", description="разбанить участника")
    async def unban(self, interaction: discord.Interaction, user: discord.User, *, reason: str = "не указана"):
        if not is_moderator(interaction.user):
            await interaction.response.send_message("нет прав", ephemeral=True)
            return

        await interaction.guild.unban(user, reason=reason)
        await self._log_action("разбан", user, interaction.user, reason, 0x00FF00)

        embed = mod_action_embed("разбан", user, interaction.user, reason, color=0x00FF00)
        embed.set_footer(text=f"модератор: {interaction.user}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="mute", description="мут участника")
    async def mute(self, interaction: discord.Interaction, member: discord.Member, duration: int = 60, *, reason: str = "не указана"):
        if not is_moderator(interaction.user):
            await interaction.response.send_message("нет прав", ephemeral=True)
            return

        if member.bot:
            await interaction.response.send_message("нельзя замутить бота", ephemeral=True)
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

        await self._log_action(f"мут ({duration} мин)", member, interaction.user, reason)

        embed = mod_action_embed(f"мут ({duration} мин)", member, interaction.user, reason)
        embed.set_footer(text=f"модератор: {interaction.user}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="unmute", description="размутить участника")
    async def unmute(self, interaction: discord.Interaction, member: discord.Member):
        if not is_moderator(interaction.user):
            await interaction.response.send_message("нет прав", ephemeral=True)
            return

        if member.bot:
            await interaction.response.send_message("нельзя размутить бота", ephemeral=True)
            return

        try:
            await member.timeout(None)
        except discord.Forbidden:
            await interaction.response.send_message("недостаточно прав", ephemeral=True)
            return

        await self._log_action("размут", member, interaction.user, "снят модератором")

        embed = mod_action_embed("размут", member, interaction.user, "снят модератором")
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

        await self._log_action(f"очистка ({deleted} сообщений)", interaction.user, interaction.user, "массовое удаление")

        embed = mod_action_embed(f"очистка ({deleted} сообщений)", interaction.user, interaction.user, "массовое удаление")
        embed.set_footer(text=f"модератор: {interaction.user}")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="warn", description="выдать предупреждение")
    async def warn(self, interaction: discord.Interaction, member: discord.Member, *, reason: str):
        if not is_moderator(interaction.user):
            await interaction.response.send_message("нет прав", ephemeral=True)
            return

        if member.bot:
            await interaction.response.send_message("нельзя предупредить бота", ephemeral=True)
            return

        warning.add(member.id, interaction.guild.id, reason, interaction.user.id)
        await self._log_action("предупреждение", member, interaction.user, reason, 0xFFFF00)

        warnings = warning.get_by_user(member.id, interaction.guild.id)
        warn_count = len(warnings)

        embed = mod_action_embed("предупреждение", member, interaction.user, f"{reason}\nвсего предупреждений: {warn_count}")
        embed.set_footer(text=f"модератор: {interaction.user}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="warnings", description="показать предупреждения")
    async def warnings(self, interaction: discord.Interaction, member: discord.Member):
        if not is_moderator(interaction.user):
            await interaction.response.send_message("нет прав", ephemeral=True)
            return

        warnings = warning.get_by_user(member.id, interaction.guild.id)

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
                value=w.reason,
                inline=False
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="unwarn", description="снять все предупреждения")
    async def unwarn(self, interaction: discord.Interaction, member: discord.Member):
        if not is_moderator(interaction.user):
            await interaction.response.send_message("нет прав", ephemeral=True)
            return

        if member.bot:
            await interaction.response.send_message("нельзя снять предупреждения бота", ephemeral=True)
            return

        warning.remove_by_user(member.id, interaction.guild.id)
        await self._log_action("предупреждения сняты", member, interaction.user, "сняты модератором")

        embed = mod_action_embed("предупреждения сняты", member, interaction.user, "сняты модератором")
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Moderation(bot))