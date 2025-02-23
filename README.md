
# 🌤️ ClimaCan

**ClimaCan** es una herramienta para la recolección, almacenamiento y visualización de datos meteorológicos de Canarias. Combina diversas APIs con una base de datos temporal y ofrece dashboards interactivos mediante [Grafana](https://grafana.com/).

---

## ✨ Características

- **Integración de APIs meteorológicas**: Obtén datos actualizados del clima en Canarias.
- **Base de datos temporal**: Almacena los datos meteorológicos utilizando [InfluxDB](https://www.influxdata.com/).
- **Visualización interactiva**: Dashboards personalizables y fáciles de usar gracias a Grafana.
- **Despliegue con un solo comando**: Configuración rápida utilizando Docker y Docker Compose.

---

## 🚀 Instalación y Uso

### 1. Requisitos previos
Antes de empezar, asegúrate de tener instalados:
- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)

### 2. Configuración
Crea un archivo `.env` en la raíz del proyecto con las siguientes variables de entorno:

```bash
# Grafana
GRAFANA_PORT=3010

# InfluxDB
INFLUXDB_PORT=8086

# PostgreSQL
POSTGRES_DB=my_db
POSTGRES_USER=my_user
POSTGRES_PASSWORD=my_pssword
POSTGRES_PORT=5435

# API Key de Grafcan
GRAFCAN_TOKEN=YOUR_API_KEY
# API Key de AEMET
AEMET_TOKEN=YOUR_API_KEY
```

> 🔑 **Nota**: Reemplaza `YOUR_API_KEY` con tu clave de acceso a la API la cual es necesaria solicitar.

### 3. Despliegue del contenedor
Una vez configurado el archivo `.env`, sigue estos pasos:
1. Ve a la carpeta `docker` del proyecto.
2. Ejecuta el comando:
   ```bash
   docker compose up -d
   ```

### 4. Acceso a la herramienta
Una vez iniciado el contenedor, accede a ClimaCan mediante tu navegador en:
[http://localhost:3010](http://localhost:3010)

---

## 📊 Dashboards de Grafana

ClimaCan incluye dashboards listos para visualizar datos como:
- Temperatura y humedad.
- Velocidad y dirección del viento.
- Pronósticos detallados.

---

## 🛠️ Tecnologías utilizadas

- **Docker & Docker Compose**: Para una configuración y despliegue rápido.
- **InfluxDB**: Base de datos temporal optimizada para datos de series temporales.
- **Grafana**: Visualización de datos mediante dashboards interactivos.
- **APIs meteorológicas**: Obtención de datos actualizados del clima en Canarias.

---

## 🤝 Contribuciones

¡Las contribuciones son bienvenidas! Si deseas colaborar:
1. Haz un fork de este repositorio.
2. Crea una rama para tu funcionalidad (`git checkout -b feature/nueva-funcionalidad`).
3. Envía un pull request con tus cambios.

---

## 📜 Licencia

Este proyecto está licenciado bajo los términos de la **MIT License**. Consulta el archivo [LICENSE](LICENSE) para más detalles.

---

## 🌐 Enlaces útiles

- Repositorio del proyecto: [ClimaCan](https://github.com/TacoronteRiveroCristian/ClimaCan)
- Documentación de Grafana: [Grafana Docs](https://grafana.com/docs/)
- Documentación de InfluxDB: [InfluxDB Docs](https://docs.influxdata.com/)
