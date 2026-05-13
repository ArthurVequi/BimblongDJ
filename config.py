import os
import google.generativeai as genai
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv

# Tokens Padrão gerados

load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')

# Gemini (IA) — usa o modelo flash
if GEMINI_API_KEY and GEMINI_API_KEY != 'sua_chave_aqui':
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-2.5-flash')
else:
    gemini_model = None

# Spotify — autenticação via Client Credentials
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
