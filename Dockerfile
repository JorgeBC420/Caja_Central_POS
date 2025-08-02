# Dockerfile para Caja Central POS
# Multi-stage build para optimizar seguridad y tamaño

# Etapa 1: Build y dependencias
FROM python:3.11-slim as builder

# Crear usuario no-root
RUN groupadd -r posuser && useradd -r -g posuser posuser

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y \
    gcc \
    libc6-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Directorio de trabajo
WORKDIR /app

# Copiar requirements y instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Etapa 2: Runtime mínimo
FROM python:3.11-slim

# Metadatos de seguridad
LABEL maintainer="bjorg@cajacentral.com"
LABEL version="1.0"
LABEL security.scan.required="true"

# Crear usuario no-root
RUN groupadd -r posuser && useradd -r -g posuser posuser

# Instalar solo dependencias de runtime críticas
RUN apt-get update && apt-get install -y \
    libsqlite3-0 \
    libssl3 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copiar dependencias Python desde builder
COPY --from=builder /root/.local /home/posuser/.local

# Crear directorios necesarios
RUN mkdir -p /app/data /app/logs /app/config /app/backups \
    && chown -R posuser:posuser /app

# Directorio de trabajo
WORKDIR /app

# Copiar código de la aplicación
COPY --chown=posuser:posuser . .

# Variables de entorno de seguridad
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production
ENV POS_DATA_DIR=/app/data
ENV POS_LOG_DIR=/app/logs
ENV POS_CONFIG_DIR=/app/config

# Exponer puerto (non-privileged)
EXPOSE 8080

# Cambiar a usuario no-root
USER posuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import sqlite3; sqlite3.connect('/app/data/caja_registradora_pos_cr.db').close()" || exit 1

# Comando por defecto
CMD ["python", "main.py"]
