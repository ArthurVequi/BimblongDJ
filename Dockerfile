FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

# Instala ffmpeg, nodejs e git (necessários para o yt-dlp decifrar o n-challenge e instalar via git)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg nodejs git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código do bot
COPY . .

CMD ["python", "bot.py"]
