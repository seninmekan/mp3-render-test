
FROM python:3.12-slim

# FFmpeg ve Deno kurulumu için gerekli araçlar
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ffmpeg \
    ca-certificates \
    curl \
    unzip && \
    rm -rf /var/lib/apt/lists/*

# Deno JavaScript çalışma ortamı
ENV DENO_INSTALL=/opt/deno

RUN curl -fsSL https://deno.land/install.sh | sh

ENV PATH="${DENO_INSTALL}/bin:${PATH}"

# Güncel yt-dlp ve YouTube JS bileşenleri
RUN pip install --no-cache-dir -U "yt-dlp[default]"

# Kurulumları doğrula
RUN deno --version && \
    yt-dlp --version && \
    ffmpeg -version

# Uygulama
WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

ENV PORT=10000

CMD ["sh", "-c", "gunicorn -b 0.0.0.0:${PORT} -w 1 --threads 2 --timeout 210 app:app"]
