# Usa una imagen ligera basada en Python
FROM python:3.12-slim

# Configurar la zona horaria de Canarias
ENV TZ=Atlantic/Canary
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Establecer directorio de trabajo
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

# Crear ususario no root
RUN groupadd --gid 1001 climacan && \
    useradd --uid 1001 --gid climacan --create-home climacan && \
    chown -R climacan:climacan /workspaces/climacan

# Cambiar al usuario no root
USER climacan

# Copiar archivo requirements.txt al contenedors
COPY requirements.txt .
# Instalar dependencias
RUN pip install --upgrade pip && pip install -r requirements.txt

# Comando de arranque
CMD ["/bin/bash"]
