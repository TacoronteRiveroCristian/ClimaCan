FROM cristiantr/dev_container_image:latest

ARG GITHUB_USERNAME
ARG GITHUB_GMAIL
ARG GRAFCAN_TOKEN
ARG WORKDIR="/workspaces/ClimaCan"

# Configurar la zona horaria de Canarias
ENV TZ=Atlantic/Canary
RUN sudo ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ | sudo tee /etc/timezone

# Crear usuario sin privilegios
USER root
RUN useradd -ms /bin/bash appuser

# Configurar credenciales de GitHub (antes del COPY)
RUN git config --global user.name "${GITHUB_USERNAME}" && \
    git config --global user.email "${GITHUB_GMAIL}"

# Copiar archivos y configurar permisos
COPY . ${WORKDIR}
RUN chown -R appuser:appuser ${WORKDIR} && \
    chmod -R 777 ${WORKDIR}

# Cambiar al usuario sin privilegios
USER appuser
WORKDIR ${WORKDIR}

# Instalar dependencias
RUN pip install --upgrade pip && pip install -r requirements.txt

# Establecer variables de entorno
ENV WORKDIR=${WORKDIR}
ENV GRAFCAN_TOKEN=${GRAFCAN_TOKEN}
ENV PYTHONPATH=${PYTHONPATH}:${WORKDIR}

# Comando de arranque
CMD ["/bin/bash"]
