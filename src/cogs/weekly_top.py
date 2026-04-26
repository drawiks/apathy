from datetime import datetime, time as dt_time
import discord
from discord.ext import commands
from discord import app_commands
from discord.ext import tasks

from config import LOG_CHANNEL, WEEKLY_TOP_ROLE, WEEKLY_TOP_DISPLAY, EMBED_COLOR, ROLE_EMOJI
from repos import redis_dota, stats
from utils.formatters import format_duration


class WeeklyTop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.weekly_check.start()

    def _format_leaderboard(self, guild: discord.Guild):
        leaderboard = redis_dota.get_leaderboard(guild.id, "dota", WEEKLY_TOP_DISPLAY)
        if not leaderboard:
            return "нет данных за эту неделю"

        lines = []

        for i, stats in enumerate(leaderboard):
            member = guild.get_member(stats.user_id)
            name = member.display_name if member else f"User {stats.user_id}"
            duration = format_duration(stats.total_seconds)
            lines.append(f"{ROLE_EMOJI[i]} **{name}** — {duration}")

        return "\n".join(lines)

    @app_commands.command(name="топ", description="показать топ игроков за неделю")
    async def топ(self, interaction: discord.Interaction):
        leaderboard_text = self._format_leaderboard(interaction.guild)

        embed = discord.Embed(
            title="🏆 топ игроков за неделю",
            description=leaderboard_text,
            color=EMBED_COLOR
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @tasks.loop(time=dt_time(hour=0, minute=0))
    async def weekly_check(self):
        now = datetime.now()
        if now.weekday() == 6:
            await self._run_weekly_top()

    async def _run_weekly_top(self):
        if not self.bot.guilds:
            return

        guild = self.bot.guilds[0]
        channel = guild.get_channel(LOG_CHANNEL)
        if not channel:
            return

        leaderboard = redis_dota.get_leaderboard(guild.id, "dota", 1)
        if not leaderboard:
            return

        winner_stats = leaderboard[0]
        winner_id = winner_stats.user_id
        winner = guild.get_member(winner_id)

        role = guild.get_role(WEEKLY_TOP_ROLE)
        if role:
            for member in guild.members:
                if role in member.roles:
                    try:
                        await member.remove_roles(role)
                    except Exception:
                        pass

            if winner:
                try:
                    await winner.add_roles(role)
                except Exception:
                    pass

        leaderboard_text = self._format_leaderboard(guild)

        embed = discord.Embed(
            title="🏆 топ игроков за неделю",
            description=leaderboard_text,
            color=EMBED_COLOR
        )

        if winner:
            embed.set_footer(text=f"победитель: {winner.display_name}")

        await channel.send(embed=embed)

        dota_stats = stats.find(game="dota")
        for stat in dota_stats:
            if stat.get("id"):
                stat["weekly_seconds"] = 0
                stats.update(stat, stat["id"])


async def setup(bot):
    await bot.add_cog(WeeklyTop(bot))