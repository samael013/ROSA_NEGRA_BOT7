"""Interface visual do ROSA NEGRA com discord.ui."""

import discord

PURPLE = discord.Color.from_rgb(123, 63, 191)
BLACK = discord.Color.from_rgb(15, 15, 18)


class MainView(discord.ui.View):
    """Menu principal com seleção rápida por botão."""

    def __init__(self, bot):
        super().__init__(timeout=300)
        self.bot = bot

    @discord.ui.select(
        placeholder="Selecione uma categoria...",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(label="OSINT & Coleta", value="osint", emoji="🔍", description="Domínios, IPs e fontes públicas"),
            discord.SelectOption(label="Análise", value="analise", emoji="📊", description="Resumos, gráficos e relatórios"),
            discord.SelectOption(label="Redes & Sistemas", value="redes", emoji="🌐", description="Ping, DNS e status autorizado"),
            discord.SelectOption(label="Dados Abertos", value="dados", emoji="📁", description="Catálogos e APIs governamentais"),
            discord.SelectOption(label="Segurança", value="seguranca", emoji="🛡️", description="Regras e privacidade"),
            discord.SelectOption(label="Meus Dados", value="meusdados", emoji="⚙️", description="Cadastro e exclusão próprios"),
        ],
    )
    async def select_category(self, interaction: discord.Interaction, select: discord.ui.Select):
        category = select.values[0]
        embeds = self.bot.category_embeds()
        await interaction.response.send_message(embed=embeds[category], ephemeral=True)


class ConsentView(discord.ui.View):
    """Confirmação explícita antes de consultas de IP."""

    def __init__(self, callback):
        super().__init__(timeout=60)
        self.callback_fn = callback

    @discord.ui.button(label="Confirmo que tenho autorização", style=discord.ButtonStyle.danger, emoji="🛡️")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.callback_fn(interaction)
        self.stop()
