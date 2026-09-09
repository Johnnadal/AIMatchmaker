FROM python:3.11-slim

# Empêcher Python de mettre en cache le bytecode
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copie et installation des dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code source
COPY . .

# IMPORTANT : --host 0.0.0.0 est obligatoire pour Google Cloud Run
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]