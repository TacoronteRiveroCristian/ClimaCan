FROM cristiantr/dev_container_image:latest

# Establecer directorio de trabajo
WORKDIR /workspaces/ClimaCan

# Copiar archivos en el directorio de trabajo
COPY . .

CMD ["/bin/bash"]
