# Usa la imagen oficial de Python 3.10.12 como base
FROM python:3.10.12-slim

# Variables de build (se pueden pasar al construir la imagen)
ARG GITHUB_USERNAME
ARG GITHUB_GMAIL
ARG GRAFCAN_TOKEN
ARG WORKDIR="/workspaces/ClimaCan"

# Configurar la zona horaria de Canarias
ENV TZ=Atlantic/Canary
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Variables de entorno
ENV WORKDIR=${WORKDIR}
ENV GRAFCAN_TOKEN=${GRAFCAN_TOKEN}
ENV PYTHONPATH=${PYTHONPATH}:${WORKDIR}

# Crear directorio de trabajo
WORKDIR ${WORKDIR}

# Instalar herramientas necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivo de dependencias
COPY requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Establecer usuario por defecto
RUN useradd -ms /bin/bash dev_container
USER dev_container

# Comando por defecto
CMD ["/bin/bash"]
