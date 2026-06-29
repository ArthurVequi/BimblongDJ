FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

# Copia o binário do Deno (JavaScript runtime recomendado para o yt-dlp resolver os desafios do YouTube)
COPY --from=denoland/deno:bin /deno /usr/local/bin/deno

# Instala o ffmpeg (necessário para áudio do Discord)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código do bot
COPY . .

CMD ["python", "bot.py"]
