import discord
import asyncio
import yt_dlp


# yt-dlp: Biblioteca busca o melhor áudio disponível, sem baixar playlists inteiras

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

# FFmpeg: reconecta automaticamente se a stream cair, e ignora vídeo (-vn = só áudio)
ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    # Transforma uma URL em fonte de áudio pro Discord.
    # Herda de PCMVolumeTransformer para permitir controle de volume.

    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        # Extrai info em thread separada para não bloquear o event loop do bot
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        # Se o resultado for uma playlist/busca, pega o primeiro item
        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


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
