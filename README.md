# 🥀 ROSA NEGRA — Bot Discord de dados públicos

Bot profissional em Python + `discord.py`, com SQLite, slash commands, menus `discord.ui`, gráficos e relatórios PDF.

## Escopo de segurança

O projeto foi desenhado para **não** consultar bases privadas, vazamentos, credenciais ou dados pessoais de terceiros. Não há comando para puxar CPF, RG, telefone, endereço, senha ou ficha de uma pessoa.

O `/ip` exige confirmação explícita de que o endereço é do usuário ou que existe autorização individual. O `/redes` é limitado a marcas, projetos e organizações e não foi implementado como ferramenta de perfilamento de pessoas.

## Requisitos

- Python 3.10+ recomendado
- Bot criado no Discord Developer Portal
- Token do bot
- Permissão `applications.commands` e `bot`

## Instalação — Windows

```powershell
cd rosa_negra_bot
py -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Edite `.env` e coloque:

```env
DISCORD_TOKEN=SEU_TOKEN
GUILD_ID=ID_DO_SEU_SERVIDOR
STATUS_URLS=https://discord.com,https://www.iana.org
```

Para testes, `GUILD_ID` faz os comandos serem sincronizados diretamente no servidor. Sem ele, os comandos são globais e a sincronização pode levar mais tempo.

Execute:

```powershell
python bot.py
```

## Instalação — Linux/Ubuntu

```bash
cd rosa_negra_bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python bot.py
```

## Comandos

### Painel
- `/org`
- `/rosanegra`
- `/rosa_negra`

### OSINT público
- `/dominio nome:exemplo.com` — DNS + RDAP público.
- `/ip endereco:... autorizado:true` — dados gerais de rede/geografia de IP público, com confirmação de autorização.
- `/busca termo:...` — busca pública sem perfilamento de pessoas.
- `/redes nome:...` — páginas públicas de marcas/projetos/organizações.

### Análise
- `/resumo fonte:...` — resumo local simples do texto fornecido.
- `/grafico dados:Janeiro=10,Fevereiro=20` — gera PNG.
- `/relatorio titulo:... conteudo:...` — gera PDF.

### Redes
- `/ping site_ip:discord.com`
- `/dns dominio_nome:example.com`
- `/status` — somente URLs definidas pelo administrador em `STATUS_URLS`.

### Dados abertos
- `/gov assunto:saúde`
- `/publicas`

### Segurança
- `/regras`
- `/aviso`
- `/licenca`

### Meus dados
- `/cadastrar`
- `/meusdados`
- `/excluir`
- `/politica`

## Fontes

- **IANA RDAP Bootstrap:** `https://data.iana.org/rdap/dns.json`
- **dados.gov.br:** API pública de catálogo
- **DNS:** resolução DNS pública através de `dnspython`
- **IP:** `https://ipwho.is/`
- **Busca pública:** DuckDuckGo Instant Answer API

## Estrutura

```text
rosa_negra_bot/
├── bot.py
├── config.py
├── db.py
├── services.py
├── ui.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── cogs/
└── data/
    └── .gitkeep
```

## Produção

1. Nunca publique `.env` no GitHub.
2. Use um token novo se o token atual vazar.
3. Restrinja `STATUS_URLS` aos serviços que você realmente administra ou tem autorização para monitorar.
4. Faça backup protegido do SQLite se o cadastro voluntário for importante.
5. Para hospedagem 24/7, use um serviço Python com armazenamento persistente para o SQLite.
6. Se transformar o projeto em produto público, publique uma política de privacidade e defina retenção, base legal e canal de atendimento adequados ao seu caso.
