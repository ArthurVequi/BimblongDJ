import discord
from discord.ext import commands



class GeneralCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # !help — Menu de ajuda customizado com embed
    @commands.command(name='help', aliases=['ajuda'], help='Mostra esta mensagem de ajuda')
    async def help_command(self, ctx):
        embed = discord.Embed(
            title="🎵 Comandos do BimbomgDJ",
            description="Aqui estão os comandos disponíveis para você usar:",
            color=discord.Color.blue()
        )

        commands_list = [
            ("!tocar <nome/link>", "Toca uma música do YouTube ou Spotify (alias: !play, !p)"),
            ("!ia <descrição>", "A IA descobre a música para você. Ex: !ia musica triste do shrek"),
            ("!pausar", "Pausa a música atual (alias: !pause)"),
            ("!retomar", "Retoma a música pausada (alias: !resume)"),
            ("!avancar", "Pula para a próxima música (alias: !pular, !skip, !next)"),
            ("!voltar", "Volta para a música anterior (alias: !back, !prev)"),
            ("!fila", "Mostra a fila de reprodução (alias: !queue, !q)"),
            ("!limpar", "Limpa todas as músicas da fila (alias: !clear, !cls)"),
            ("!sair", "Desconecta o bot (alias: !leave, !stop)"),
            ("!help", "Mostra esta mensagem (alias: !ajuda)")
        ]

        for name, value in commands_list:
            embed.add_field(name=name, value=value, inline=False)

        embed.set_footer(text="TheBestApeDJ")
        await ctx.send(embed=embed)


# Função de setup para carregar o Cog no bot
async def setup(bot):
    await bot.add_cog(GeneralCommands(bot))
