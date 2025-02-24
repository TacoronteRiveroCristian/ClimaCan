# Usa una imagen ligera basada en Python
FROM python:3.12-slim

# Establecer directorio de trabajo
ENV PYTHONPATH=/workspaces/climacan
WORKDIR /workspaces/climacan

# Actualizar el sistema e instalar dependencias necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    lsof \
    git-all \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no root
RUN groupadd --gid 1001 climacan && \
    useradd --uid 1001 --gid climacan --create-home climacan && \
    chown -R climacan:climacan /workspaces/climacan

# Copiar archivo requirements.txt
COPY requirements.txt .

# Instalar dependencias
RUN pip install --upgrade pip && pip install -r requirements.txt

# Comando de arranque con Bash interactivo
CMD ["/bin/bash"]
