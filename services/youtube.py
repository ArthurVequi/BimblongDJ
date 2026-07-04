import discord
import asyncio
import yt_dlp
import os

import shutil

# Se houver cookies do YouTube nas variáveis de ambiente, salva em um arquivo local
youtube_cookies = os.getenv('YOUTUBE_COOKIES')
if youtube_cookies:
    try:
        # Garante que limpa o caractere carriage return do windows
        youtube_cookies = youtube_cookies.replace('\r\n', '\n')
        with open('cookies.txt', 'w', encoding='utf-8') as f:
            f.write(youtube_cookies)
        print(f"✅ Cookies do YouTube carregados das variáveis de ambiente ({len(youtube_cookies)} bytes).")
    except Exception as e:
        print(f"⚠️ Erro ao salvar cookies do YouTube: {e}")

# Verifica se o Deno está presente no sistema (runtime JS recomendado pelo yt-dlp)
deno_path = shutil.which('deno')
if deno_path:
    print(f"✅ Deno encontrado no path: {deno_path}")
else:
    print("⚠️ Deno NÃO encontrado no path! Desafios de JS do YouTube podem falhar.")

# yt-dlp: Biblioteca busca o melhor áudio disponível, sem baixar playlists inteiras
ytdl_format_options = {
    # MUDANÇA CRÍTICA: O YouTube está bloqueando ativamente as streams exclusivas de áudio (bestaudio) em datacenters.
    # Ao pedir o formato 'best' (vídeo + áudio), nós driblamos a proteção 403, e o FFmpeg extrai o áudio normalmente!
    'format': 'best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': True,
    'quiet': False,
    'no_warnings': False,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    # Melhoria: Priorizar codecs de áudio melhores (como opus)
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'opus',
        'preferredquality': '192',
    }],
    'remote_components': {'ejs:github'},
    # Remove clientes defeituosos que causam 403 e força o default
    'extractor_args': {'youtube': {'player_client': ['default', '-android_sdkless']}},
}

if os.getenv('YOUTUBE_BROWSER'):
    browser = os.getenv('YOUTUBE_BROWSER')
    ytdl_format_options['cookiesfrombrowser'] = (browser,)
    print(f"🍪 ytdl_format_options configurado com cookiesfrombrowser='{browser}'")
elif os.path.exists('cookies.txt'):
    ytdl_format_options['cookiefile'] = 'cookies.txt'
    print("🍪 ytdl_format_options configurado com cookiefile='cookies.txt'")
else:
    print("🍪 ytdl_format_options NÃO está usando arquivo de cookies e nem cookies do navegador.")

# FFmpeg: otimizado para streaming de alta qualidade, reconexão rápida e normalização de áudio
ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -filter:a "loudnorm=I=-16:TP=-1.5:LRA=11" -b:a 192k'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)



class YTDLSource(discord.PCMVolumeTransformer):
    # Transforma uma URL em fonte de áudio pro Discord.
    # Herda de PCMVolumeTransformer para permitir controle de volume.

    def __init__(self, source, *, data, volume=1.0, filename=None):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.filename = filename

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        # Extrai info em thread separada para não bloquear o event loop do bot
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        # Se o resultado for uma playlist/busca, pega o primeiro item
        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)

        # Copia as opções globais do ffmpeg para não modificar o dicionário original
        opts = ffmpeg_options.copy()

        # Passa o arquivo de cookies e o User-Agent pro ffmpeg, essencial para evitar o Erro 403 Forbidden do YouTube
        if stream:
            if os.path.exists('cookies.txt'):
                opts['before_options'] += ' -cookies "cookies.txt"'
            
            if 'http_headers' in data:
                ua = data['http_headers'].get('User-Agent')
                if ua:
                    opts['before_options'] += f' -user_agent "{ua}"'

        return cls(discord.FFmpegPCMAudio(filename, **opts), data=data, filename=filename if not stream else None)


async def search_youtube(query):
    # Busca no YouTube pelo nome da música. Retorna (url, title) ou None.
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
