import discord
from discord.ext import commands
import yt_dlp
import google.generativeai as genai
import os
import re
from dotenv import load_dotenv
import asyncio
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# Carrega variáveis de ambiente
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')

# Configura o Gemini (IA)
if GEMINI_API_KEY and GEMINI_API_KEY != 'sua_chave_aqui':
    genai.configure(api_key=GEMINI_API_KEY)
    # Recomendado o flash por ser rápido
    model = genai.GenerativeModel('gemini-2.5-flash')
else:
    model = None

# Configura o Spotify
if SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET and SPOTIFY_CLIENT_ID != 'seu_client_id_aqui':
    try:
        sp_credentials = SpotifyClientCredentials(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET)
        sp = spotipy.Spotify(client_credentials_manager=sp_credentials)
        print('✅ Spotify configurado com sucesso!')
    except Exception as e:
        sp = None
        print(f'⚠️ Erro ao configurar Spotify: {e}')
else:
    sp = None
    print('⚠️ Spotify não configurado. Adicione SPOTIFY_CLIENT_ID e SPOTIFY_CLIENT_SECRET no .env para usar links do Spotify.')

# Configura o Bot com o prefixo !
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)
bot.remove_command('help')


# Opções do yt-dlp e ffmpeg
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        # Não baixa, só pega a info para a stream
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        # O ffmpeg precisa estar instalado no PC
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

# Gerenciador de estado por servidor (Guild)
class MusicState:
    def __init__(self):
        self.queue = []
        self.history = []
        self.current = None

music_states = {}

def get_state(guild_id):
    if guild_id not in music_states:
        music_states[guild_id] = MusicState()
    return music_states[guild_id]

def is_spotify_url(url):
    """Verifica se a URL é do Spotify."""
    return bool(re.match(r'https?://open\.spotify\.com/(?:intl-[a-z]{2}/)?(track|playlist|album)/', url))

async def get_spotify_tracks(url):
    """Extrai nomes de músicas de um link do Spotify (track, playlist ou álbum)."""
    if not sp:
        return None, 'Spotify não está configurado. Adicione suas credenciais no arquivo `.env`.'
    
    try:
        # Extrai o tipo e ID do link
        match = re.match(r'https?://open\.spotify\.com/(?:intl-[a-z]{2}/)?(track|playlist|album)/([a-zA-Z0-9]+)', url)
        if not match:
            return None, 'Link do Spotify inválido.'
        
        link_type = match.group(1)
        spotify_id = match.group(2)
        tracks = []
        
        if link_type == 'track':
            track = sp.track(spotify_id)
            artist = track['artists'][0]['name']
            name = track['name']
            tracks.append(f"{artist} - {name}")
        
        elif link_type == 'playlist':
            results = sp.playlist_tracks(spotify_id)
            for item in results['items']:
                track = item.get('track')
                if track:
                    artist = track['artists'][0]['name']
                    name = track['name']
                    tracks.append(f"{artist} - {name}")
            # Paginação: playlists grandes têm mais de 100 músicas
            while results['next']:
                results = sp.next(results)
                for item in results['items']:
                    track = item.get('track')
                    if track:
                        artist = track['artists'][0]['name']
                        name = track['name']
                        tracks.append(f"{artist} - {name}")
        
        elif link_type == 'album':
            results = sp.album_tracks(spotify_id)
            album_info = sp.album(spotify_id)
            for track in results['items']:
                artist = track['artists'][0]['name']
                name = track['name']
                tracks.append(f"{artist} - {name}")
        
        if not tracks:
            return None, 'Não encontrei músicas nesse link do Spotify.'
        
        return tracks, None
    except Exception as e:
        return None, f'Erro ao acessar o Spotify: {e}'

async def search_youtube(query):
    """Busca uma música no YouTube pelo nome e retorna (url, title) ou None."""
    try:
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(f"ytsearch:{query}", download=False))
        if 'entries' in data and len(data['entries']) > 0:
            info = data['entries'][0]
            video_url = info.get('webpage_url') or info.get('url')
            title = info.get('title')
            return (video_url, title)
    except:
        pass
    return None

async def play_next(ctx):
    state = get_state(ctx.guild.id)
    if len(state.queue) > 0:
        url, title = state.queue.pop(0)
        
        async with ctx.typing():
            try:
                # Extrai a stream em tempo real para não expirar (YouTube streams expiram rápido)
                player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
                
                # Quando acabar, chama o play_next novamente
                def after_playing(e):
                    if e:
                        print(f'Erro no player: {e}')
                    # Roda o próximo passo
                    coro = play_next(ctx)
                    fut = asyncio.run_coroutine_threadsafe(coro, bot.loop)
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

@bot.event
async def on_ready():
    print(f'✅ {bot.user} conectado com sucesso!')
    print('Esperando comandos com o prefixo "!"')

# --- Comandos do Bot ---

@bot.command(name='tocar', aliases=['play', 'p'], help='Toca uma música a partir de um link ou nome. Ex: !tocar despacito')
async def tocar(ctx, *, url):
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
            # Verifica se é um link do Spotify
            if is_spotify_url(url):
                tracks, error = await get_spotify_tracks(url)
                if error:
                    await ctx.send(f'❌ {error}')
                    return
                
                await ctx.send(f'<:spotify:🟢> Encontradas **{len(tracks)}** música(s) do Spotify. Buscando no YouTube...')
                
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
            
            # Se for um link direto (YouTube, etc.), não usa ytsearch
            search_query = url if url.startswith('http') else f"ytsearch:{url}"
            
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(search_query, download=False))
            
            # Link direto: yt-dlp retorna o vídeo sem a chave 'entries'
            # Pesquisa por nome: retorna uma lista em 'entries'
            if 'entries' in data:
                info = data['entries'][0] if len(data['entries']) > 0 else None
            else:
                info = data  # É um link direto, o resultado já é o vídeo

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

@bot.command(name='ia', help='Descreve uma música e a IA vai tentar descobrir e tocar. Ex: !ia aquela musica do shrek')
async def ia(ctx, *, prompt):
    if not model:
        await ctx.send("⚠️ A Chave da API do Gemini não foi configurada. Coloque-a no arquivo `.env` para usar esse comando.")
        return
    
    async with ctx.typing():
        try:
            # Pede para a IA descobrir a música
            ai_prompt = f"O usuário está pedindo uma música com a seguinte descrição: '{prompt}'. Retorne APENAS o nome exato da música e o artista/banda para que eu possa pesquisar no YouTube. Não adicione nenhum outro texto, aspas, ou explicação."
            response = await asyncio.to_thread(model.generate_content, ai_prompt)
            search_query = response.text.strip()
            
            await ctx.send(f"🧠 A IA interpretou seu pedido como: **{search_query}**\nBuscando...")
            
            # Conecta se não estiver
            if not ctx.message.author.voice:
                await ctx.send("Você não está conectado a um canal de voz.")
                return
                
            channel = ctx.message.author.voice.channel
            if not ctx.voice_client:
                await channel.connect()
            elif ctx.voice_client.channel != channel:
                await ctx.voice_client.move_to(channel)

            state = get_state(ctx.guild.id)
            
            # Busca no YouTube com o resultado da IA
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
            await ctx.send(f"❌ Erro na IA ou busca: {e}")

@bot.command(name='pausar', aliases=['pause'], help='Pausa a música atual')
async def pausar(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸️ Música pausada. Use !retomar para voltar.")
    else:
        await ctx.send("Não estou tocando nada no momento.")

@bot.command(name='retomar', aliases=['resume'], help='Retoma a música pausada')
async def retomar(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶️ Música retomada.")
    else:
        await ctx.send("A música não está pausada.")

@bot.command(name='avancar', aliases=['pular', 'skip', 'next'], help='Pula para a próxima música')
async def avancar(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        state = get_state(ctx.guild.id)
        if state.current:
            state.history.append(state.current)
        ctx.voice_client.stop() # Parar aciona a próxima música da fila
        await ctx.send("⏭️ Música pulada.")
    else:
        await ctx.send("Não estou tocando nada para pular.")

@bot.command(name='voltar', aliases=['back', 'prev'], help='Volta para a música anterior')
async def voltar(ctx):
    state = get_state(ctx.guild.id)
    if len(state.history) > 0:
        # Pega a ultima música do historico
        last_song_url, last_song_title = state.history.pop()
        
        # Coloca a atual no topo da fila (para não perder) se houver uma tocando
        if state.current:
            state.queue.insert(0, state.current)
        
        # Coloca a música anterior no topo da fila (como a próxima a tocar)
        state.queue.insert(0, (last_song_url, last_song_title))
        
        if ctx.voice_client and ctx.voice_client.is_playing():
            # Parar aciona o play_next, que vai pegar a música que acabamos de colocar no index 0
            ctx.voice_client.stop() 
        else:
            await play_next(ctx)
            
        await ctx.send(f"⏪ Voltando para: **{last_song_title}**")
    else:
         await ctx.send("Não há músicas no histórico recente.")

@bot.command(name='fila', aliases=['queue', 'q'], help='Mostra a fila de músicas')
async def fila(ctx):
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

@bot.command(name='limpar', aliases=['clear', 'cls'], help='Limpa todas as músicas da fila')
async def limpar(ctx):
    state = get_state(ctx.guild.id)
    state.queue.clear()
    await ctx.send("🧹 A fila foi limpa com sucesso!")

@bot.command(name='sair', aliases=['leave', 'stop'], help='Desconecta o bot do canal de voz')
async def sair(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        # Limpar estado
        if ctx.guild.id in music_states:
            del music_states[ctx.guild.id]
        await ctx.send("👋 Desconectado do canal de voz.")
    else:
         await ctx.send("Não estou em um canal de voz.")

@bot.command(name='help', aliases=['ajuda'], help='Mostra esta mensagem de ajuda')
async def help_command(ctx):
    embed = discord.Embed(
        title="🎵 Comandos do BimbomgDJ",
        description="Aqui estão os comandos disponíveis para você usar:",
        color=discord.Color.blue()
    )
    
    # Lista de comandos com descrições
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
    
    embed.set_footer(text="Desenvolvido por Antigravity AI")
    await ctx.send(embed=embed)

if __name__ == '__main__':

    if not DISCORD_TOKEN or DISCORD_TOKEN == 'seu_token_aqui':
        print("AVISO: DISCORD_TOKEN não configurado. Por favor edite o arquivo .env.")
    else:
        try:
            bot.run(DISCORD_TOKEN)
        except Exception as e:
            print(f"Erro ao iniciar o bot (verifique o token): {e}")
