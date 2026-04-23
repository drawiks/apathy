from datetime import datetime
import discord
from discord.ext import commands
from discord import app_commands
from discord.ext import tasks

from config import GAME_CHANNEL, WEEKLY_TOP_ROLE, WEEKLY_TOP_DISPLAY, EMBED_COLOR
from utils.redis import redis_client


class WeeklyTop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.weekly_check.start()

    def _format_duration(self, seconds: int):
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        if hours > 0:
            return f"{hours}ч {minutes}м"
        return f"{minutes}м"

    def _format_leaderboard(self, guild: discord.Guild):
        leaderboard = redis_client.get_weekly_leaderboard(WEEKLY_TOP_DISPLAY)
        if not leaderboard:
            return "нет данных за эту неделю"

        lines = []
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]

        for i, (user_id, seconds) in enumerate(leaderboard):
            member = guild.get_member(user_id)
            name = member.display_name if member else f"User {user_id}"
            duration = self._format_duration(seconds)
            lines.append(f"{medals[i]} **{name}** — {duration}")

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

    @tasks.loop(time=datetime.time(hour=0, minute=0))
    async def weekly_check(self):
        now = datetime.now()
        if now.weekday() == 6:
            await self._run_weekly_top()

    async def _run_weekly_top(self):
        if not self.bot.guilds:
            return

        guild = self.bot.guilds[0]
        channel = guild.get_channel(GAME_CHANNEL)
        if not channel:
            return

        leaderboard = redis_client.get_weekly_leaderboard(1)
        if not leaderboard:
            return

        winner_id, _ = leaderboard[0]
        winner = guild.get_member(winner_id)

        if winner:
            role = guild.get_role(WEEKLY_TOP_ROLE)
            if role:
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

        redis_client.reset_weekly()


async def setup(bot):
    await bot.add_cog(WeeklyTop(bot))