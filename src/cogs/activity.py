from datetime import datetime
import discord
from discord import app_commands
from discord.ext import commands

from config import GAME_CHANNEL, GAME_NAME, DOTA_JOIN_GIF, DOTA_LEAVE_GIF, EMBED_COLOR
from utils.redis import redis_client


class Activity(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _get_gif_path(self, action: str):
        return DOTA_JOIN_GIF if action == "join" else DOTA_LEAVE_GIF

    def _format_duration(self, seconds: int):
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        if hours > 0:
            return f"{hours}ч {minutes}м"
        return f"{minutes}м"

    @commands.Cog.listener()
    async def on_presence_update(self, before, after):
        if after.bot:
            return

        channel = self.bot.get_channel(GAME_CHANNEL)
        if not channel:
            return

        before_dota = before.activities and any(
            a.type == discord.ActivityType.playing and a.name == GAME_NAME
            for a in before.activities if hasattr(a, 'type')
        )
        after_dota = after.activities and any(
            a.type == discord.ActivityType.playing and a.name == GAME_NAME
            for a in after.activities if hasattr(a, 'type')
        )

        if after_dota and not before_dota:
            timestamp = datetime.now().timestamp()
            redis_client.set_online(after.id, timestamp)

            timestamp_str = datetime.now().strftime("%H:%M")
            gif_path = self._get_gif_path("join")
            file = discord.File(gif_path)
            member_color = after.colour if after.colour != discord.Colour.default() else EMBED_COLOR
            embed = discord.Embed(
                title=f"{after.display_name} ({after.name}) запустил доту",
                color=member_color
            )
            embed.set_image(url=f"attachment://{gif_path}")
            embed.set_footer(text=f"время: {timestamp_str}")
            await channel.send(embed=embed, file=file)

        elif before_dota and not after_dota:
            start_timestamp = redis_client.get_online(after.id)
            if start_timestamp:
                duration_seconds = int(datetime.now().timestamp() - start_timestamp)
                redis_client.add_play_time(after.id, duration_seconds)
                redis_client.remove_online(after.id)

            timestamp_str = datetime.now().strftime("%H:%M")
            gif_path = self._get_gif_path("leave")
            file = discord.File(gif_path)
            member_color = after.colour if after.colour != discord.Colour.default() else EMBED_COLOR
            embed = discord.Embed(
                title=f"{after.display_name} ({after.name}) вышел из доты",
                color=member_color
            )
            embed.set_image(url=f"attachment://{gif_path}")
            embed.set_footer(text=f"время: {timestamp_str}")
            await channel.send(embed=embed, file=file)

    @app_commands.command(name="online", description="показать игроков в доте")
    async def online(self, interaction: discord.Interaction):
        online_data = redis_client.get_all_online()

        if not online_data:
            await interaction.response.send_message("сейчас никто не играет в доту", ephemeral=True)
            return

        now = datetime.now().timestamp()
        embed = discord.Embed(
            title="сейчас в доте:",
            color=EMBED_COLOR
        )

        for user_id, start_time in online_data:
            member = interaction.guild.get_member(user_id)
            if member:
                duration = int(now - start_time)
                embed.add_field(
                    name=member.display_name,
                    value=self._format_duration(duration),
                    inline=False
                )

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Activity(bot))