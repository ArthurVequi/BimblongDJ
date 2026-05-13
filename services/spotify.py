import re
from config import sp



def is_spotify_url(url):
    # Identifica links do Spotify (track, playlist, album)
    return bool(re.match(r'https?://open\.spotify\.com/(?:intl-[a-z]{2}/)?(track|playlist|album)/', url))


async def get_spotify_tracks(url):
    # Converte um link do Spotify em lista de strings "Artista - Nome da Música".
    if not sp:
        return None, 'Spotify não está configurado. Adicione suas credenciais no arquivo `.env`.'

    try:
        # Extrai o tipo (track/playlist/album) e o ID do link, caso não encontre retorna None
        match = re.match(r'https?://open\.spotify\.com/(?:intl-[a-z]{2}/)?(track|playlist|album)/([a-zA-Z0-9]+)', url)
        if not match:
            return None, 'Link do Spotify inválido.'

        link_type = match.group(1)
        spotify_id = match.group(2)
        tracks = []

        # Verifica o tipo de link e extrai as músicas

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
                    
            # Paginação para playlists com mais de 100 faixas
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
