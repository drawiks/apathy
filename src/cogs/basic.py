import discord
from discord import app_commands
from discord.ext import commands

from config import EMBED_COLOR, BASE_ROLE, ROLE_CHANNEL, ROLE_POSITIONS, ROLE_EMOJI
from core.checks import is_moderator
from core.embeds import success_embed
from services import stats_repo, role_message_repo
from utils.formatters import format_duration


class Basic(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ping", description="проверить задержку бота")
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        embed = success_embed("pong", f"задержка: {latency}мс")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="команды", description="список команд бота")
    async def commands_list(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="список команд",
            color=EMBED_COLOR
        )

        embed.add_field(
            name="основные",
            value="/ping - проверить задержку\n/команды - этот список\n/voice [user] - время в голосовых\n/voice_top - топ",
            inline=False
        )

        if is_moderator(interaction.user):
            embed.add_field(
                name="модерация",
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

    @app_commands.command(name="салам", description="дебаг: показать приветственное сообщение")
    async def salam(self, interaction: discord.Interaction):
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

    @app_commands.command(name="roles", description="отправить сообщение для выбора ролей")
    async def roles(self, interaction: discord.Interaction):
        if not is_moderator(interaction.user):
            await interaction.response.send_message("нет прав", ephemeral=True)
            return

        embed = success_embed("выбери позицию (можно несколько)", "нажми на эмодзи для получения роли")

        msg = await interaction.channel.send(embed=embed)

        for emoji, role_id in ROLE_POSITIONS.items():
            await msg.add_reaction(emoji)
            role_message_repo.add(interaction.guild.id, msg.id, emoji, role_id)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.guild_id is None:
            return
        if payload.user_id == self.bot.user.id:
            return

        role_messages = role_message_repo.get_by_message(payload.message_id)
        for rm in role_messages:
            if rm.emoji == str(payload.emoji):
                guild = self.bot.get_guild(payload.guild_id)
                if guild:
                    member = guild.get_member(payload.user_id)
                    role = guild.get_role(rm.role_id)
                    if member and role:
                        try:
                            await member.add_roles(role)
                        except discord.Forbidden:
                            pass

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.guild_id is None:
            return
        if payload.user_id == self.bot.user.id:
            return

        role_messages = role_message_repo.get_by_message(payload.message_id)
        for rm in role_messages:
            if rm.emoji == str(payload.emoji):
                guild = self.bot.get_guild(payload.guild_id)
                if guild:
                    member = guild.get_member(payload.user_id)
                    role = guild.get_role(rm.role_id)
                    if member and role:
                        try:
                            await member.remove_roles(role)
                        except discord.Forbidden:
                            pass

    @app_commands.command(name="voice", description="показать время в голосовых")
    async def voice(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        total_seconds = stats_repo.get_total(target.id, interaction.guild.id, "voice")
        
        if total_seconds == 0:
            await interaction.response.send_message(f"{target.display_name} ещё не был в голосовых", ephemeral=True)
            return
        
        time_str = format_duration(total_seconds)
        embed = success_embed("голосовые", f"{target.display_name} - {time_str}")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="voice_top", description="топ по голосовым")
    async def voice_top(self, interaction: discord.Interaction):
        leaderboard = stats_repo.get_leaderboard(interaction.guild.id, "voice", 5)
        
        if not leaderboard:
            await interaction.response.send_message("нет данных", ephemeral=True)
        
        lines = []
        for i, stats in enumerate(leaderboard):
            member = interaction.guild.get_member(stats.user_id)
            name = member.display_name if member else f"User {stats.user_id}"
            time_str = format_duration(stats.total_seconds)
            lines.append(f"{ROLE_EMOJI[i]} **{name}** - {time_str}")
        
        embed = discord.Embed(
            title="топ по голосовым",
            description="\n".join(lines),
            color=EMBED_COLOR
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Basic(bot))