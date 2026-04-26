from datetime import datetime
import discord
from discord import app_commands
from discord.ext import commands

from config import GAME_CHANNEL, GAME_NAME, DOTA_JOIN_GIF, DOTA_LEAVE_GIF, EMBED_COLOR
from services import redis_client, stats_repo
from utils.formatters import format_duration


class Activity(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _get_gif_path(self, action: str):
        return DOTA_JOIN_GIF if action == "join" else DOTA_LEAVE_GIF

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
            redis_client.set_online(f"dota:{after.id}", timestamp)

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
            start_timestamp = redis_client.get_online(f"dota:{after.id}")
            duration_seconds = 0
            if start_timestamp:
                duration_seconds = int(datetime.now().timestamp() - start_timestamp)
                redis_client.remove_online(f"dota:{after.id}")

                if after.guild:
                    stats_repo.add_time(
                        after.id, 
                        after.guild.id, 
                        "dota", 
                        duration_seconds
                    )

            session_time = format_duration(duration_seconds)

            timestamp_str = datetime.now().strftime("%H:%M")
            gif_path = self._get_gif_path("leave")
            file = discord.File(gif_path)
            member_color = after.colour if after.colour != discord.Colour.default() else EMBED_COLOR
            embed = discord.Embed(
                title=f"{after.display_name} ({after.name}) вышел из доты",
                description=f"наиграл: {session_time}",
                color=member_color
            )
            embed.set_image(url=f"attachment://{gif_path}")
            embed.set_footer(text=f"время: {timestamp_str}")
            await channel.send(embed=embed, file=file)

    @app_commands.command(name="online", description="показать игроков в доте")
    async def online(self, interaction: discord.Interaction):
        keys = redis_client.client.keys("dota:*")
        
        if not keys:
            await interaction.response.send_message("сейчас никто не играет в доту", ephemeral=True)
            return

        embed = discord.Embed(
            title="сейчас в доте:",
            color=EMBED_COLOR
        )

        for key in keys:
            user_id = int(key.split(":")[1])
            member = interaction.guild.get_member(user_id)
            if member:
                embed.add_field(
                    name=member.display_name,
                    value="•",
                    inline=False
                )

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Activity(bot))