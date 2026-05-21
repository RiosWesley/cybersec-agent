FROM python:3.10-slim

# Instala dependências do sistema necessárias para compilar llama-cpp-python em CPU
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    make \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia os requerimentos e instala as dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código da aplicação
COPY . .

# Cria a pasta para o modelo
RUN mkdir -p models

# Expõe a porta do FastAPI
EXPOSE 8000

# Script de entrada que baixa o modelo se ele não existir e depois inicia a API
RUN echo '#!/bin/bash\n\
python download_model.py\n\
uvicorn app:app --host 0.0.0.0 --port 8000\n\
' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
