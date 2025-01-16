FROM cristiantr/dev_container_image:latest

ARG GITHUB_USERNAME
ARG GITHUB_GMAIL
ARG GRAFCAN_TOKEN
ARG WORKDIR="/workspaces/ClimaCan"

# Configurar la zona horaria de Canarias
ENV TZ=Atlantic/Canary
RUN sudo ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ | sudo tee /etc/timezone

# Establecer variables de entorno
ENV WORKDIR=${WORKDIR}
ENV GRAFCAN_TOKEN=${GRAFCAN_TOKEN}
ENV PYTHONPATH=${PYTHONPATH}:${WORKDIR}

# Crear usuario sin privilegios
USER root

# Configurar credenciales de GitHub (antes del COPY)
RUN git config --global user.name "${GITHUB_USERNAME}" && \
    git config --global user.email "${GITHUB_GMAIL}"

# Copiar archivos y configurar permisos
WORKDIR ${WORKDIR}
COPY . .
RUN chown -R dev_container:dev_container ${WORKDIR} && \
    chmod -R 770 ${WORKDIR} && \
    chmod 600 ${WORKDIR}/.env

# Cambiar al usuario sin privilegios
USER dev_container

# Crear entorno virtual y instalar dependencias
RUN python3 -m venv .venv && \
    .venv/bin/pip install --upgrade pip

# Comando de arranque
CMD ["/bin/bash"]
