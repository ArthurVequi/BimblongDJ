

class MusicState:
    def __init__(self):
        self.queue = []      # Fila de reprodução: lista com tuplas de (url, title)
        self.history = []    # Histórico de músicas já tocadas (para o comando !voltar)
        self.current = None  # Recebe o nome da música tocando no momento


# Dicionário global que mapeia guild_id → MusicState
music_states = {}

# Retorna (ou cria) o estado de música do servidor.
def get_state(guild_id):
    if guild_id not in music_states:
        music_states[guild_id] = MusicState()
    return music_states[guild_id]
