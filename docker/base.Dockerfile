FROM cristiantr/dev_container_image:latest

ARG GITHUB_USERNAME
ARG GITHUB_TOKEN
ARG GITHUB_GMAIL
ARG GRAFCAN_TOKEN
ARG WORKDIR="/workspaces/ClimaCan"

# Configurar credenciales de GitHub (uso con precaución)
RUN git config --global credential.helper 'store' && \
    echo "https://${GITHUB_USERNAME}:${GITHUB_TOKEN}@github.com" > ~/.git-credentials && \
    git config --global user.name "${GITHUB_USERNAME}" && \
    git config --global user.email "${GITHUB_GMAIL}"

# Establecer directorio de trabajo
WORKDIR ${WORKDIR}

# Copiar archivos en el directorio de trabajo
COPY . .

# Instalar dependencias
RUN pip install -r requirements.txt

# Establecer variables de entorno
ENV WORKDIR=${WORKDIR}
ENV GRAFCAN_TOKEN=${GRAFCAN_TOKEN}
ENV PYTHONPATH=${PYTHONPATH}:${WORKDIR}

# Comando de arranque
CMD ["/bin/bash"]
