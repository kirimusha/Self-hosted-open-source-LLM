FROM python:3.10-slim

WORKDIR /app

# Устанавливаем зависимости для сборки
RUN apt-get update && apt-get install -y \
    g++ \
    make \
    cmake \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем llama-cpp-python (CPU версия, легкая)
RUN pip install --no-cache-dir llama-cpp-python==0.2.26 fastapi==0.104.1 uvicorn[standard]==0.24.0

COPY server.py .

EXPOSE 8080

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]