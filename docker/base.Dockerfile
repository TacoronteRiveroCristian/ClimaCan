FROM cristiantr/dev_container_image:latest

# Agregar credenciales de GH al contenedor
RUN git config --global credential.helper 'store' && \
    echo "https://${GITHUB_USERNAME}:${GITHUB_TOKEN}@github.com" > ~/.git-credentials


# Establecer directorio de trabajo
WORKDIR /workspaces/ClimaCan

# Copiar archivos en el directorio de trabajo
COPY . .

CMD ["/bin/bash"]
