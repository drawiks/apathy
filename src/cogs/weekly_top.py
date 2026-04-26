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
        keys = redis_dota.get_all("weekly:*")
        if not keys:
            return "нет данных за эту неделю"

        users = []
        for key in keys:
            try:
                key_str = key.replace("dota:weekly:", "")
                user_id = int(key_str)
                seconds = int(redis_dota.get(key)) or 0
                users.append((user_id, seconds))
            except (ValueError, TypeError):
                continue

        if not users:
            return "нет данных за эту неделю"

        users.sort(key=lambda x: x[1], reverse=True)
        users = users[:WEEKLY_TOP_DISPLAY]

        lines = []
        for i, (user_id, seconds) in enumerate(users, 1):
            member = guild.get_member(user_id)
            name = member.display_name if member else f"User {user_id}"
            duration = format_duration(seconds)
            lines.append(f"{ROLE_EMOJI[i-1]} **{name}** — {duration}")

        return "\n".join(lines)

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

        keys = redis_dota.get_all("weekly:*")
        if not keys:
            return

        users = []
        for key in keys:
            try:
                key_str = key.replace("dota:weekly:", "")
                user_id = int(key_str)
                seconds = int(redis_dota.get(key)) or 0
                users.append((user_id, seconds))
            except (ValueError, TypeError):
                continue

        if not users:
            return

        users.sort(key=lambda x: x[1], reverse=True)
        winner_id = users[0][0] if users else None
        winner = guild.get_member(winner_id) if winner_id else None

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