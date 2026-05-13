import asyncio
from music.state import get_state
from services.youtube import YTDLSource



async def play_next(ctx):
    # Pega a próxima música da fila, faz stream e toca.
    # Ao terminar, chama a si mesmo recursivamente via callback.
    state = get_state(ctx.guild.id)
    if len(state.queue) > 0:
        url, title = state.queue.pop(0)

        async with ctx.typing():
            try:
                # Stream em tempo real, não baixa o arquivo inteiro
                player = await YTDLSource.from_url(url, loop=ctx.bot.loop, stream=True)

                # Callback executado quando a música termina — agenda play_next de forma thread-safe
                def after_playing(e):
                    if e:
                        print(f'Erro no player: {e}')
                    coro = play_next(ctx)
                    fut = asyncio.run_coroutine_threadsafe(coro, ctx.bot.loop)
                    try:
                        fut.result()
                    except:
                        pass

                ctx.voice_client.play(player, after=after_playing)
                state.current = (url, title)
                await ctx.send(f'🎵 Tocando agora: **{title}**')
            except Exception as e:
                await ctx.send(f'❌ Erro ao tocar a música: {e}')
                await play_next(ctx)
    else:
        state.current = None
        await ctx.send('A fila acabou. Adicione mais músicas!')
