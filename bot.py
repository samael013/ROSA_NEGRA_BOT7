"""ROSA NEGRA — bot Discord de dados públicos e autoatendimento.

Todos os comandos são slash commands. O bot não possui mecanismo para
consultar dados privados, vazamentos, credenciais, telefone de terceiros,
CPF, endereço residencial ou perfis pessoais agregados.
"""

import io
import json
import os
from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

import config
import db
from services import (
    ServiceError, dns_records, domain_rdap, gov_search, ip_public_info,
    ping_host, public_search, url_status, normalize_domain
)
from ui import MainView, ConsentView, PURPLE


INTENTS = discord.Intents.default()


class RosaNegra(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=INTENTS)

    async def setup_hook(self):
        await db.init_db()
        # Se GUILD_ID estiver configurado, sincroniza imediatamente nesse servidor.
        if config.GUILD_ID.isdigit():
            guild = discord.Object(id=int(config.GUILD_ID))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            print(f"Slash commands sincronizados na guild {config.GUILD_ID}.")
        else:
            await self.tree.sync()
            print("Slash commands globais sincronizados.")

    async def on_ready(self):
        print(f"ROSA NEGRA online como {self.user} (ID {self.user.id})")
        await self.change_presence(activity=discord.Game(name="Dados públicos • /rosanegra"))

    def main_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🟣 BEM-VINDO À ROSA NEGRA 🟣",
            description="**Sistema de Análise e Inteligência de Dados Públicos**",
            color=PURPLE,
        )
        embed.add_field(name="🔍 1. OSINT & COLETA DE DADOS PÚBLICOS", value="→ Domínios, DNS, RDAP, IPs públicos e fontes abertas", inline=False)
        embed.add_field(name="📊 2. ANÁLISE E VISUALIZAÇÃO", value="→ Processa e organiza dados e gera gráficos/relatórios", inline=False)
        embed.add_field(name="🌐 3. REDES & SISTEMAS", value="→ Conectividade, DNS e monitoramento de URLs autorizadas", inline=False)
        embed.add_field(name="📁 4. DADOS ABERTOS OFICIAIS", value="→ Consulta o catálogo público dados.gov.br", inline=False)
        embed.add_field(name="🛡️ 5. SEGURANÇA & BOAS PRÁTICAS", value="→ Privacidade, limites e uso ético", inline=False)
        embed.add_field(name="⚙️ 6. MEUS DADOS & CONFIGURAÇÕES", value="→ Cadastro voluntário, consulta e exclusão próprios", inline=False)
        embed.set_footer(text="Use os botões abaixo ou os comandos / do ROSA NEGRA.")
        return embed

    def category_embeds(self):
        return {
            "osint": discord.Embed(title="🔍 OSINT & COLETA", description="Use /dominio, /ip, /busca e /redes. Somente informações públicas e dentro dos limites deste bot.", color=PURPLE),
            "analise": discord.Embed(title="📊 ANÁLISE", description="Use /resumo, /grafico e /relatorio para transformar dados fornecidos por você em resultados organizados.", color=PURPLE),
            "redes": discord.Embed(title="🌐 REDES & SISTEMAS", description="Use /ping, /dns e /status. O /status monitora somente URLs configuradas pelo administrador.", color=PURPLE),
            "dados": discord.Embed(title="📁 DADOS ABERTOS", description="Use /gov para consultar o catálogo público do dados.gov.br e /publicas para ver as fontes liberadas.", color=PURPLE),
            "seguranca": discord.Embed(title="🛡️ SEGURANÇA", description="Use /regras, /aviso e /licenca para conhecer os limites de uso.", color=PURPLE),
            "meusdados": discord.Embed(title="⚙️ MEUS DADOS", description="Use /cadastrar, /meusdados, /excluir e /politica. O bot só armazena informações fornecidas voluntariamente pelo próprio usuário.", color=PURPLE),
        }

    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        message = f"❌ Não foi possível concluir o comando: `{error}`"
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)


bot = RosaNegra()


async def send_error(interaction: discord.Interaction, message: str):
    if interaction.response.is_done():
        await interaction.followup.send(f"❌ {message}", ephemeral=True)
    else:
        await interaction.response.send_message(f"❌ {message}", ephemeral=True)


@bot.tree.command(name="org", description="Abre o painel principal da ROSA NEGRA")
async def org(interaction: discord.Interaction):
    await interaction.response.send_message(embed=bot.main_embed(), view=MainView(bot))


@bot.tree.command(name="rosanegra", description="Abre o painel principal da ROSA NEGRA")
async def rosanegra(interaction: discord.Interaction):
    await interaction.response.send_message(embed=bot.main_embed(), view=MainView(bot))


@bot.tree.command(name="rosa_negra", description="Abre o painel principal da ROSA NEGRA")
async def rosa_negra(interaction: discord.Interaction):
    await interaction.response.send_message(embed=bot.main_embed(), view=MainView(bot))


@bot.tree.command(name="dominio", description="Consulta RDAP e DNS públicos de um domínio")
@app_commands.describe(nome="Ex.: exemplo.com")
async def dominio(interaction: discord.Interaction, nome: str):
    await interaction.response.defer(thinking=True)
    try:
        domain = normalize_domain(nome)
        rdap, dns = await __import__('asyncio').gather(domain_rdap(domain), dns_records(domain))
        embed = discord.Embed(title=f"🔍 Domínio: {domain}", color=PURPLE)
        entities = rdap.get("entities", [])
        embed.add_field(name="RDAP", value=f"Servidor consultado: público/RDAP\nEntidades públicas retornadas: {len(entities)}", inline=False)
        for typ, values in dns.items():
            text = "\n".join(values[:5]) or "—"
            embed.add_field(name=f"DNS {typ}", value=f"```{text[:900]}```", inline=False)
        await interaction.followup.send(embed=embed)
    except ServiceError as exc:
        await send_error(interaction, str(exc))


@bot.tree.command(name="ip", description="Consulta dados gerais de um IP público com autorização")
@app_commands.describe(endereco="IP público", autorizado="Marque somente se o IP é seu ou você tem autorização para consultá-lo")
async def ip_cmd(interaction: discord.Interaction, endereco: str, autorizado: bool):
    if not autorizado:
        await send_error(interaction, "Por privacidade, /ip exige confirmação de que você é proprietário do IP ou possui autorização individual.")
        return
    await interaction.response.defer(ephemeral=True, thinking=True)
    try:
        data = await ip_public_info(endereco)
        embed = discord.Embed(title=f"🌐 IP público: {data.get('ip', endereco)}", color=PURPLE)
        embed.add_field(name="Localização aproximada", value=f"{data.get('city') or '—'} / {data.get('region') or '—'} / {data.get('country') or '—'}", inline=False)
        embed.add_field(name="Provedor/ASN", value=f"{data.get('connection', {}).get('isp') or '—'} / AS{data.get('connection', {}).get('asn') or '—'}", inline=False)
        embed.set_footer(text="Dados aproximados de rede; não identificam uma pessoa.")
        await interaction.followup.send(embed=embed, ephemeral=True)
    except ServiceError as exc:
        await send_error(interaction, str(exc))


@bot.tree.command(name="busca", description="Pesquisa informações públicas sem perfilamento de pessoas")
@app_commands.describe(termo="Tema, organização, projeto, domínio ou assunto público")
async def busca(interaction: discord.Interaction, termo: str):
    await interaction.response.defer(thinking=True)
    try:
        if any(word in termo.lower() for word in ("cpf", "rg", "telefone", "celular", "endereço", "senha", "email pessoal", "documento")):
            raise ServiceError("Consultas destinadas a localizar ou agregar dados pessoais não são permitidas.")
        results = await public_search(termo)
        embed = discord.Embed(title=f"🔎 Busca pública: {termo[:80]}", color=PURPLE)
        if not results:
            embed.description = "Nenhum resultado público foi retornado pela fonte consultada."
        else:
            for item in results[:6]:
                url = item.get("url") or ""
                embed.add_field(name=item.get("title", "Resultado")[:200], value=(item.get("text", "")[:700] + (f"\n{url}" if url else "")), inline=False)
        await interaction.followup.send(embed=embed)
    except ServiceError as exc:
        await send_error(interaction, str(exc))


@bot.tree.command(name="redes", description="Localiza páginas públicas de uma marca/projeto/organização")
@app_commands.describe(nome="Nome de marca, projeto ou organização; não use nome de pessoa")
async def redes(interaction: discord.Interaction, nome: str):
    await interaction.response.defer(thinking=True)
    try:
        if len(nome.strip()) < 2 or any(x in nome.lower() for x in ("cpf", "telefone", "email", "rg")):
            raise ServiceError("Informe uma marca, projeto ou organização. O bot não faz agregação de perfis pessoais.")
        results = await public_search(f"{nome} site:github.com OR site:youtube.com OR site:instagram.com OR site:facebook.com")
        embed = discord.Embed(title=f"🌐 Páginas públicas: {nome[:80]}", color=PURPLE)
        for item in results[:8]:
            if item.get("url"):
                embed.add_field(name=item.get("title", "Página")[:180], value=item["url"][:1000], inline=False)
        if not results:
            embed.description = "Nenhuma página pública foi encontrada."
        await interaction.followup.send(embed=embed)
    except ServiceError as exc:
        await send_error(interaction, str(exc))


@bot.tree.command(name="resumo", description="Resume texto fornecido pelo usuário")
@app_commands.describe(fonte="Cole o conteúdo público que deseja organizar")
async def resumo(interaction: discord.Interaction, fonte: str):
    if len(fonte) > 3500:
        await send_error(interaction, "O texto deve ter no máximo 3500 caracteres.")
        return
    # Resumo local e determinístico: sem enviar o conteúdo a um serviço externo.
    sentences = [s.strip() for s in fonte.replace("\n", " ").split(".") if s.strip()]
    selected = sentences[:8]
    embed = discord.Embed(title="📊 Resumo", description="\n• " + "\n• ".join(selected) if selected else "Sem conteúdo.", color=PURPLE)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="grafico", description="Gera gráfico a partir de pares rótulo=valor")
@app_commands.describe(dados="Ex.: Janeiro=10,Fevereiro=20,Março=15")
async def grafico(interaction: discord.Interaction, dados: str):
    try:
        pairs = []
        for item in dados.split(","):
            label, value = item.split("=", 1)
            pairs.append((label.strip(), float(value.strip().replace(",", "."))))
        if not 1 <= len(pairs) <= 20:
            raise ValueError
    except ValueError:
        await send_error(interaction, "Formato inválido. Use `Nome=valor,Nome=valor` com até 20 itens.")
        return
    await interaction.response.defer(ephemeral=True, thinking=True)
    labels, values = zip(*pairs)
    fig = plt.figure(figsize=(8, 4.5))
    plt.bar(labels, values)
    plt.title("ROSA NEGRA — Análise de dados fornecidos")
    plt.xticks(rotation=35, ha="right")
    plt.tight_layout()
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=160)
    plt.close(fig)
    buffer.seek(0)
    await interaction.followup.send(file=discord.File(buffer, filename="rosa_negra_grafico.png"), ephemeral=True)


@bot.tree.command(name="relatorio", description="Gera PDF com dados fornecidos pelo usuário")
@app_commands.describe(titulo="Título do relatório", conteudo="Conteúdo do relatório")
async def relatorio(interaction: discord.Interaction, titulo: str, conteudo: str):
    if len(conteudo) > 8000 or len(titulo) > 120:
        await send_error(interaction, "Título ou conteúdo muito grande.")
        return
    await interaction.response.defer(ephemeral=True, thinking=True)
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 60
    pdf.setTitle(titulo)
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, y, titulo[:100])
    y -= 30
    pdf.setFont("Helvetica", 9)
    pdf.drawString(50, y, "ROSA NEGRA • relatório criado somente a partir do conteúdo fornecido pelo usuário")
    y -= 30
    pdf.setFont("Helvetica", 10)
    for paragraph in conteudo.splitlines() or [conteudo]:
        words = paragraph.split()
        line = ""
        for word in words:
            if pdf.stringWidth(line + " " + word, "Helvetica", 10) > width - 100:
                pdf.drawString(50, y, line)
                y -= 15
                line = word
                if y < 50:
                    pdf.showPage(); y = height - 50; pdf.setFont("Helvetica", 10)
            else:
                line = (line + " " + word).strip()
        if line:
            pdf.drawString(50, y, line); y -= 15
        if y < 50:
            pdf.showPage(); y = height - 50; pdf.setFont("Helvetica", 10)
    pdf.save()
    buffer.seek(0)
    await interaction.followup.send(file=discord.File(buffer, filename="rosa_negra_relatorio.pdf"), ephemeral=True)


@bot.tree.command(name="ping", description="Verifica conectividade TCP de um host público")
@app_commands.describe(site_ip="Ex.: discord.com ou 1.1.1.1:443")
async def ping(interaction: discord.Interaction, site_ip: str):
    await interaction.response.defer(thinking=True)
    result = await ping_host(site_ip)
    if result["ok"]:
        await interaction.followup.send(f"🏓 **{result['host']}:{result['port']}** respondeu em **{result['ms']:.1f} ms**.")
    else:
        await interaction.followup.send(f"❌ **{result['host']}:{result['port']}** não respondeu dentro do limite.\n`{result.get('error', 'erro')[:300]}`")


@bot.tree.command(name="dns", description="Lista registros DNS públicos de um domínio")
@app_commands.describe(dominio_nome="Ex.: exemplo.com")
async def dns(interaction: discord.Interaction, dominio_nome: str):
    await interaction.response.defer(thinking=True)
    try:
        data = await dns_records(dominio_nome)
        embed = discord.Embed(title=f"📡 DNS: {normalize_domain(dominio_nome)}", color=PURPLE)
        for typ, values in data.items():
            embed.add_field(name=typ, value="\n".join(values[:6]) or "—", inline=False)
        await interaction.followup.send(embed=embed)
    except ServiceError as exc:
        await send_error(interaction, str(exc))


@bot.tree.command(name="status", description="Monitora os URLs configurados pelo administrador")
async def status(interaction: discord.Interaction):
    if not config.STATUS_URLS:
        await send_error(interaction, "Nenhum serviço foi configurado em STATUS_URLS no .env.")
        return
    await interaction.response.defer(thinking=True)
    results = await __import__('asyncio').gather(*(url_status(u) for u in config.STATUS_URLS[:20]))
    embed = discord.Embed(title="🟢 Status de serviços autorizados", color=PURPLE)
    for item in results:
        icon = "🟢" if item["ok"] else "🔴"
        latency = f"{item['ms']:.1f} ms" if item["ms"] is not None else "indisponível"
        embed.add_field(name=f"{icon} {item['url']}", value=f"HTTP: `{item['status']}` • Latência: `{latency}`", inline=False)
    await interaction.followup.send(embed=embed)


@bot.tree.command(name="gov", description="Consulta o catálogo público de dados do governo")
@app_commands.describe(assunto="Assunto ou palavra-chave")
async def gov(interaction: discord.Interaction, assunto: str):
    await interaction.response.defer(thinking=True)
    try:
        data = await gov_search(assunto)
        results = data.get("result", {}).get("results", [])
        embed = discord.Embed(title=f"📁 Dados.gov.br: {assunto[:80]}", color=PURPLE)
        for item in results[:8]:
            url = f"https://dados.gov.br/dados/conjuntos-dados/{item.get('name')}" if item.get("name") else ""
            embed.add_field(name=item.get("title", "Conjunto")[:200], value=(item.get("notes") or "Sem descrição")[:500] + (f"\n{url}" if url else ""), inline=False)
        if not results:
            embed.description = "Nenhum conjunto encontrado."
        await interaction.followup.send(embed=embed)
    except ServiceError as exc:
        await send_error(interaction, str(exc))


@bot.tree.command(name="publicas", description="Lista fontes públicas utilizadas pelo bot")
async def publicas(interaction: discord.Interaction):
    embed = discord.Embed(title="📚 Fontes públicas", color=PURPLE)
    embed.add_field(name="IANA RDAP", value="Bootstrap oficial para localizar servidores RDAP por TLD.", inline=False)
    embed.add_field(name="DNS", value="Resolvedor DNS público/recursivo via dnspython; sem banco privado.", inline=False)
    embed.add_field(name="dados.gov.br", value="Catálogo/API pública de dados abertos do governo brasileiro.", inline=False)
    embed.add_field(name="IP público", value="ipwho.is para dados gerais de rede/geografia aproximada, mediante confirmação de autorização.", inline=False)
    embed.add_field(name="Busca pública", value="DuckDuckGo Instant Answer API; sem enumeração de pessoas.", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="regras", description="Exibe regras de uso ético e legal")
async def regras(interaction: discord.Interaction):
    text = ("**Uso permitido:** domínios, DNS, RDAP, conectividade e dados abertos.\n\n"
            "**Proibido:** CPF/RG/telefone/endereço de terceiros, credenciais, vazamentos, bases privadas, stalking, doxxing, invasão ou tentativa de contornar controles.\n\n"
            "O usuário é responsável por ter autorização para qualquer ativo que não seja público e por respeitar a LGPD e os Termos do Discord.")
    await interaction.response.send_message(embed=discord.Embed(title="🛡️ Regras", description=text, color=PURPLE), ephemeral=True)


@bot.tree.command(name="aviso", description="Orientações de privacidade e limites")
async def aviso(interaction: discord.Interaction):
    await interaction.response.send_message("🛡️ **Privacidade:** o ROSA NEGRA não fornece ferramenta de busca de pessoas nem consulta vazamentos. O cadastro é voluntário e os dados cadastrados podem ser excluídos pelo próprio usuário.", ephemeral=True)


@bot.tree.command(name="licenca", description="Informações sobre conformidade e software")
async def licenca(interaction: discord.Interaction):
    await interaction.response.send_message("⚖️ O projeto usa `discord.py` sob licença MIT e foi estruturado para consultar apenas fontes públicas. A conformidade jurídica do uso concreto depende do operador, finalidade e jurisdição; o bot não substitui orientação jurídica.", ephemeral=True)


@bot.tree.command(name="cadastrar", description="Cadastra voluntariamente seus próprios dados")
@app_commands.describe(nome="Seu próprio nome", email="Seu próprio e-mail", observacao="Uma observação opcional")
async def cadastrar(interaction: discord.Interaction, nome: str, email: str, observacao: str = ""):
    if len(nome) > 120 or len(email) > 254 or len(observacao) > 1000:
        await send_error(interaction, "Um dos campos excedeu o limite permitido.")
        return
    await db.save_user(interaction.user.id, nome, email, observacao)
    await interaction.response.send_message("✅ Seus dados foram cadastrados/atualizados. Somente você poderá consultá-los ou excluí-los através deste bot.", ephemeral=True)


@bot.tree.command(name="meusdados", description="Exibe somente seus dados cadastrados")
async def meusdados(interaction: discord.Interaction):
    row = await db.get_user(interaction.user.id)
    if not row:
        await interaction.response.send_message("ℹ️ Você ainda não possui cadastro. Use /cadastrar.", ephemeral=True)
        return
    embed = discord.Embed(title="⚙️ Meus dados", color=PURPLE)
    embed.add_field(name="Nome", value=row["nome"] or "—", inline=False)
    embed.add_field(name="E-mail", value=row["email"] or "—", inline=False)
    embed.add_field(name="Observação", value=row["observacao"] or "—", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="excluir", description="Exclui completamente seu cadastro voluntário")
async def excluir(interaction: discord.Interaction):
    deleted = await db.delete_user(interaction.user.id)
    await interaction.response.send_message("🗑️ Seus dados foram excluídos do banco local." if deleted else "ℹ️ Você não possuía dados cadastrados.", ephemeral=True)


@bot.tree.command(name="politica", description="Exibe a política de privacidade do bot")
async def politica(interaction: discord.Interaction):
    text = ("**ROSA NEGRA — Política de Privacidade**\n\n"
            "1. O banco local guarda somente dados enviados voluntariamente pelo próprio usuário em /cadastrar.\n"
            "2. O Discord ID é usado como chave técnica para impedir que um usuário veja o cadastro de outro.\n"
            "3. /meusdados mostra somente o próprio registro.\n"
            "4. /excluir remove o registro voluntário do banco local.\n"
            "5. Consultas externas usam fontes públicas e não criam um banco de perfis de terceiros.\n"
            "6. O administrador deve proteger o token do bot, o arquivo `.env` e o banco SQLite.\n\n"
            f"Política externa: {config.PRIVACY_URL or 'não configurada'}")
    await interaction.response.send_message(embed=discord.Embed(title="🔐 Política de Privacidade", description=text, color=PURPLE), ephemeral=True)


if __name__ == "__main__":
    bot.run(config.DISCORD_TOKEN)
