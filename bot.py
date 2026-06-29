import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import discord
from discord.ext import commands
from config import DISCORD_TOKEN

# Entry point — inicializa o bot

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Remove o comando !help padrão do discord.py
bot.remove_command('help')

#  Chama quando o bot está online
@bot.event
async def on_ready():
    print(f'✅ {bot.user} conectado com sucesso!')
    print('Esperando comandos com o prefixo "!"')


async def load_cogs():
    # Carrega todos os módulos de comando do bot.
    await bot.load_extension('commands.music_commands')
    await bot.load_extension('commands.general')


@bot.event
async def setup_hook():
    # Hook chamado automaticamente pelo discord.py antes do bot ficar pronto.
    await load_cogs()


# Iniciando o bot
if __name__ == '__main__':
    if not DISCORD_TOKEN or DISCORD_TOKEN == 'seu_token_aqui':
        print("AVISO: DISCORD_TOKEN não configurado. Por favor edite o arquivo .env.")
    else:
        try:
            bot.run(DISCORD_TOKEN)
        except Exception as e:
            print(f"Erro ao iniciar o bot (verifique o token): {e}")
