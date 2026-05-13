# 🎵 BimblongDJ

Um bot de música avançado para o Discord construído em Python. O **BimblongDJ** suporta reprodução de áudio diretamente do YouTube e Spotify, além de contar com uma integração com Inteligência Artificial (Google Gemini) para encontrar a música certa a partir de uma descrição que você der!

## ✨ Funcionalidades

- **YouTube & Spotify:** Toca músicas usando o nome, links diretos do YouTube ou links do Spotify (faixa, álbum ou playlist).
- **Busca por IA:** Não lembra o nome da música? Use a IA para descrever a música (ex: "*aquela música triste do filme do Shrek*") e o bot acha ela para você!
- **Controle de Fila:** Sistema completo de fila por servidor, com histórico e paginação.
- **Controles de Reprodução:** Pausar, retomar, avançar, voltar e limpar fila.
- **Arquitetura Modular:** Código limpo e moderno utilizando `Cogs` e divisão em pacotes lógicos (serviços, música e comandos).

## 🛠️ Tecnologias Utilizadas

- [Python 3.10+](https://www.python.org/)
- [discord.py](https://discordpy.readthedocs.io/) - Interação com a API do Discord.
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - Busca e extração de áudio do YouTube.
- [FFmpeg](https://ffmpeg.org/) - Processamento do streaming de áudio.
- [Spotipy](https://spotipy.readthedocs.io/) - Integração com a API do Spotify.
- [Google Generative AI](https://ai.google.dev/) - Inteligência Artificial para a busca por prompt.

## 🚀 Como instalar e rodar localmente

### 1. Pré-requisitos
Você vai precisar ter instalado no seu PC:
- Python (versão 3.10 ou superior).
- O **[FFmpeg](https://ffmpeg.org/download.html)** instalado e adicionado ao `PATH` do seu sistema (obrigatório para que o bot consiga transmitir o áudio pro Discord).

### 2. Clonar o repositório
```bash
git clone https://github.com/ArthurVequi/BimblongDJ.git
cd BimblongDJ
```

### 3. Instalar as dependências
Recomenda-se criar um ambiente virtual (`venv`) antes de instalar:
```bash
pip install -r requirements.txt
```

### 4. Configurar as Chaves de API
Crie um arquivo chamado `.env` na raiz do projeto (use o `.env.example` como base) e preencha com as suas chaves:

```env
DISCORD_TOKEN=seu_token_do_bot_aqui
GEMINI_API_KEY=sua_chave_do_google_aqui
SPOTIFY_CLIENT_ID=seu_client_id_do_spotify_aqui
SPOTIFY_CLIENT_SECRET=seu_client_secret_do_spotify_aqui
```

### 5. Executar o bot
Com tudo configurado, basta rodar o arquivo principal:
```bash
python bot.py
```

## 📜 Comandos Disponíveis

O prefixo padrão do bot é `!`

| Comando | Aliases | Descrição |
| :--- | :--- | :--- |
| `!tocar <nome/link>` | `!play`, `!p` | Adiciona e toca uma música (YouTube/Spotify). |
| `!ia <descrição>` | - | Usa a Inteligência Artificial para descobrir qual música tocar. |
| `!pausar` | `!pause` | Pausa a música atual. |
| `!retomar` | `!resume` | Volta a tocar a música pausada. |
| `!avancar` | `!pular`, `!skip`, `!next`| Pula a música atual e vai para a próxima. |
| `!voltar` | `!back`, `!prev` | Volta a tocar a música anterior. |
| `!fila` | `!queue`, `!q` | Exibe a fila atual de músicas. |
| `!limpar` | `!clear`, `!cls` | Limpa toda a fila de reprodução. |
| `!sair` | `!leave`, `!stop` | Desconecta o bot do canal de voz e apaga a fila. |
| `!help` | `!ajuda` | Mostra o menu de ajuda customizado. |

---
**Desenvolvido com 🐒 por TheBestApeDJ.**
