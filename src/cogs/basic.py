import discord
from discord import app_commands
from discord.ext import commands

from config import EMBED_COLOR, BASE_ROLE, ROLE_CHANNEL
from utils.checks import is_moderator


class Basic(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ping", description="проверить задержку бота")
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        embed = discord.Embed(
            title="pong",
            description=f"задержка: {latency}мс",
            color=EMBED_COLOR
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="команды", description="список команд бота")
    async def commands_list(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="список команд",
            color=EMBED_COLOR
        )

        embed.add_field(
            name="основные",
            value="/ping - проверить задержку\n/команды - этот список",
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

        ROLE_POSITIONS = {
            "1️⃣": 1424326184585531543,
            "2️⃣": 1424326316945309696,
            "3️⃣": 1424326347676975206,
            "4️⃣": 1424326409970516070,
            "5️⃣": 1424326450651336714,
        }

        embed = discord.Embed(
            title="выбери позицию (можно несколько)",
            description="нажми на эмодзи для получения роли",
            color=EMBED_COLOR
        )

        await interaction.response.send_message(embed=embed)
        msg = await interaction.original_response()

        for emoji in ROLE_POSITIONS.keys():
            await msg.add_reaction(emoji)

        if interaction.guild.id not in self.bot.role_messages:
            self.bot.role_messages[interaction.guild.id] = {}
        self.bot.role_messages[interaction.guild.id][msg.id] = ROLE_POSITIONS


async def setup(bot):
    await bot.add_cog(Basic(bot))