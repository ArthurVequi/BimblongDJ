import discord
from discord.ext import commands
import asyncio
from music.state import get_state, music_states
from music.player import play_next
from services.youtube import search_youtube, ytdl
from services.spotify import is_spotify_url, get_spotify_tracks
from services.ai import interpret_music_request


#  Comandos de música do bot

class MusicCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    #  !tocar — Aceita: nome de música, link do YouTube ou link do Spotify (track/playlist/album)
    @commands.command(name='tocar', aliases=['play', 'p'], help='Toca uma música a partir de um link ou nome. Ex: !tocar despacito')
    async def tocar(self, ctx, *, url):
        if not ctx.message.author.voice:
            await ctx.send("Você precisa estar em um canal de voz para tocar música.")
            return

        channel = ctx.message.author.voice.channel
        if not ctx.voice_client:
            await channel.connect()
        elif ctx.voice_client.channel != channel:
            await ctx.voice_client.move_to(channel)

        state = get_state(ctx.guild.id)

        async with ctx.typing():
            try:
                # Fluxo Spotify: extrai os nomes das faixas e busca cada uma no YouTube
                if is_spotify_url(url):
                    tracks, error = await get_spotify_tracks(url)
                    if error:
                        await ctx.send(f'❌ {error}')
                        return

                    await ctx.send(f'🟢 Encontradas **{len(tracks)}** música(s) do Spotify. Buscando no YouTube...')

                    added = 0
                    for track_name in tracks:
                        result = await search_youtube(track_name)
                        if result:
                            state.queue.append(result)
                            added += 1

                    await ctx.send(f'✅ **{added}/{len(tracks)}** músicas adicionadas à fila!')

                    if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
                        await play_next(ctx)
                    return

                # Fluxo padrão: se for URL direta usa ela, senão faz busca no YouTube
                search_query = url if url.startswith('http') else f"ytsearch:{url}"

                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(None, lambda: ytdl.extract_info(search_query, download=False))

                # Link direto retorna os dados do vídeo; busca por nome retorna em 'entries'
                if 'entries' in data:
                    info = data['entries'][0] if len(data['entries']) > 0 else None
                else:
                    info = data

                if info:
                    video_url = info.get('webpage_url') or info.get('url')
                    title = info.get('title')

                    state.queue.append((video_url, title))
                    await ctx.send(f'✅ Adicionado à fila: **{title}**')

                    if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
                        await play_next(ctx)
                else:
                    await ctx.send("Não consegui encontrar resultados para essa busca.")
            except Exception as e:
                await ctx.send(f'Ocorreu um erro ao buscar a música: {str(e)}')

    # !ia — Usa o Gemini para interpretar descrições vagas e encontrar a música certa
    @commands.command(name='ia', help='Descreve uma música e a IA vai tentar descobrir e tocar. Ex: !ia aquela musica do shrek')
    async def ia(self, ctx, *, prompt):
        async with ctx.typing():
            search_query, error = await interpret_music_request(prompt)
            if error:
                await ctx.send(error)
                return

            await ctx.send(f"🧠 A IA interpretou seu pedido como: **{search_query}**\nBuscando...")

            if not ctx.message.author.voice:
                await ctx.send("Você não está conectado a um canal de voz.")
                return

            channel = ctx.message.author.voice.channel
            if not ctx.voice_client:
                await channel.connect()
            elif ctx.voice_client.channel != channel:
                await ctx.voice_client.move_to(channel)

            state = get_state(ctx.guild.id)

            try:
                # Busca o resultado da IA no YouTube
                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(None, lambda: ytdl.extract_info(f"ytsearch:{search_query}", download=False))

                if 'entries' in data and len(data['entries']) > 0:
                    info = data['entries'][0]
                    video_url = info.get('webpage_url') or info.get('url')
                    title = info.get('title')

                    state.queue.append((video_url, title))
                    await ctx.send(f'✅ Adicionado à fila (Descoberto por IA): **{title}**')

                    if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
                        await play_next(ctx)
                else:
                    await ctx.send("Não consegui encontrar resultados no YouTube para a música que a IA encontrou.")
            except Exception as e:
                await ctx.send(f"❌ Erro na busca: {e}")

    # !pausar / !retomar — Controles básicos de reprodução
    @commands.command(name='pausar', aliases=['pause'], help='Pausa a música atual')
    async def pausar(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send("⏸️ Música pausada. Use !retomar para voltar.")
        else:
            await ctx.send("Não estou tocando nada no momento.")

    @commands.command(name='retomar', aliases=['resume'], help='Retoma a música pausada')
    async def retomar(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send("▶️ Música retomada.")
        else:
            await ctx.send("A música não está pausada.")

    # !avancar — Para a música atual; o callback after_playing dispara play_next automaticamente
    @commands.command(name='avancar', aliases=['pular', 'skip', 'next'], help='Pula para a próxima música')
    async def avancar(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            state = get_state(ctx.guild.id)
            if state.current:
                state.history.append(state.current)
            ctx.voice_client.stop()
            await ctx.send("⏭️ Música pulada.")
        else:
            await ctx.send("Não estou tocando nada para pular.")

    # !voltar — Rearranja a fila: coloca a música anterior no topo e empurra a atual pra frente
    @commands.command(name='voltar', aliases=['back', 'prev'], help='Volta para a música anterior')
    async def voltar(self, ctx):
        state = get_state(ctx.guild.id)
        if len(state.history) > 0:
            last_song_url, last_song_title = state.history.pop()

            # Preserva a música atual colocando-a como próxima na fila
            if state.current:
                state.queue.insert(0, state.current)

            # A música anterior vai pro topo da fila — play_next vai pegá-la
            state.queue.insert(0, (last_song_url, last_song_title))

            if ctx.voice_client and ctx.voice_client.is_playing():
                ctx.voice_client.stop()  # stop() dispara play_next via callback
            else:
                await play_next(ctx)

            await ctx.send(f"⏪ Voltando para: **{last_song_title}**")
        else:
            await ctx.send("Não há músicas no histórico recente.")

    # !fila — Mostra até 10 músicas da fila atual
    @commands.command(name='fila', aliases=['queue', 'q'], help='Mostra a fila de músicas')
    async def fila(self, ctx):
        state = get_state(ctx.guild.id)
        if len(state.queue) == 0:
            await ctx.send("A fila está vazia.")
        else:
            fila_str = "🎵 **Fila atual:**\n"
            for i, (url, title) in enumerate(state.queue[:10]):
                fila_str += f"{i+1}. {title}\n"
            if len(state.queue) > 10:
                fila_str += f"... e mais {len(state.queue) - 10} músicas."
            await ctx.send(fila_str)

    # !limpar — Esvazia a fila sem desconectar o bot
    @commands.command(name='limpar', aliases=['clear', 'cls'], help='Limpa todas as músicas da fila')
    async def limpar(self, ctx):
        state = get_state(ctx.guild.id)
        state.queue.clear()
        await ctx.send("🧹 A fila foi limpa com sucesso!")

    # !sair — Desconecta e limpa todo o estado do servidor
    @commands.command(name='sair', aliases=['leave', 'stop'], help='Desconecta o bot do canal de voz')
    async def sair(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            if ctx.guild.id in music_states:
                del music_states[ctx.guild.id]
            await ctx.send("👋 Desconectado do canal de voz.")
        else:
            await ctx.send("Não estou em um canal de voz.")


async def setup(bot):
    await bot.add_cog(MusicCommands(bot))
