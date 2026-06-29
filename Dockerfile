FROM python:3.11-slim

# Instala ffmpeg e nodejs (nodejs é exigido pelo yt-dlp para resolver verificações do YouTube)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg nodejs && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código do bot
COPY . .

CMD ["python", "bot.py"]
