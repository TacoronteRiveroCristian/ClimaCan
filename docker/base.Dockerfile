FROM cristiantr/dev_container_image:latest

# Argumentos de construcción
ARG GITHUB_USERNAME
ARG GITHUB_GMAIL
ARG GITHUB_TOKEN
ARG WORKSPACES

# Configurar credenciales de GitHub (uso con precaución)
RUN git config --global credential.helper 'store' && \
    echo "https://${GITHUB_USERNAME}:${GITHUB_TOKEN}@github.com" > ~/.git-credentials && \
    git config --global user.name "${GITHUB_USERNAME}" && \
    git config --global user.email "${GITHUB_GMAIL}"

# Establecer variables de entorno
ENV WORKSPACES=${WORKSPACES}
ENV PYTHONPATH="${WORKSPACES}:${PYTHONPATH}"
ENV GRAFCAN_TOKEN=${GRAFCAN_TOKEN}

# Establecer directorio de trabajo
WORKDIR ${WORKSPACES}

# Copiar archivos en el directorio de trabajo
COPY . .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Instalar pre-commit hooks
# RUN pre-commit install

# Comando de arranque
CMD ["/bin/bash"]
