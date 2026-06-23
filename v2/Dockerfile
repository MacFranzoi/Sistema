# Sistema Plug 2.0 — backend FastAPI + frontend estático
# Build a partir da RAIZ do repositório:  docker build -f v2/Dockerfile .
FROM python:3.11-slim

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instala dependências do v2
COPY v2/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o api.py (lógica compartilhada) e os dados/caches da raiz
COPY api.py .
COPY *.json ./
COPY listas ./listas

# Copia o backend + frontend do v2
COPY v2/main.py .
COPY v2/static ./static

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Railway injeta a porta via $PORT
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
