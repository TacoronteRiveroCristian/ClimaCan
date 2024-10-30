FROM cristiantr/dev_container_image:latest

# Agregar credenciales de GH al contenedor
ARG GITHUB_USERNAME
ARG GITHUB_TOKEN

# Agregar credenciales de GH al contenedor
RUN git config --global credential.helper 'store' && \
    echo "https://${GITHUB_USERNAME}:${GITHUB_TOKEN}@github.com" > ~/.git-credentials

# Configurar el usuario y el correo de Git globalmente
RUN git config --global user.name "Your Name" && \
    git config --global user.email "your.email@example.com"

# Establecer directorio de trabajo
WORKDIR /workspaces/ClimaCan

# Copiar archivos en el directorio de trabajo
COPY . .

# Instalar dependencias
RUN pip install -r requirements.txt

# Añadir el directorio de trabajo al PYTHONPATH
ENV PYTHONPATH="/workspaces/ClimaCan:${PYTHONPATH}"

# Definir el directorio del proyecto como variable de entorno
ENV ROOT_PROJECT=/workspaces/ClimaCan

# Instalar pre-commit
RUN pre-commit install

CMD ["/bin/bash"]
