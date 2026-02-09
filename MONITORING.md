# Monitoreo del Sistema ClimaCan

## Verificación de Salud del Sistema

### 1. Estado de los Contenedores
```bash
docker ps | grep climacan
```
Todos los contenedores deben estar "Up".

### 2. Verificar Logs de AEMET
```bash
docker logs climacan-dev --tail=50 | grep AEMET
```

### 3. Verificar Logs de Grafcan
```bash
docker logs climacan-dev --tail=50 | grep Grafcan
```

### 4. Verificar Últimos Datos en InfluxDB

#### Predicciones AEMET (deben actualizarse cada 6 horas)
```bash
docker exec climacan-dev python3 -c "
from influxdb import InfluxDBClient
import os
client = InfluxDBClient(host='climacan-influxdb', port=int(os.getenv('INFLUXDB_PORT')))
client.switch_database('Adeje')
result = client.query('SELECT * FROM \"temperatura\" ORDER BY time DESC LIMIT 1')
for point in result.get_points():
    print(f'Último dato: {point.get(\"time\")}')"
```

#### Observaciones Convencionales AEMET (deben actualizarse cada hora)
```bash
docker exec climacan-dev python3 -c "
from influxdb import InfluxDBClient
import os
client = InfluxDBClient(host='climacan-influxdb', port=int(os.getenv('INFLUXDB_PORT')))
client.switch_database('aemet_conventional_observations')
result = client.query('SELECT * FROM \"adeje_caldera_b\" ORDER BY time DESC LIMIT 1')
for point in result.get_points():
    print(f'Último dato: {point.get(\"time\")}')"
```

#### Observaciones Grafcan (deben actualizarse cada 10 minutos)
```bash
docker exec climacan-dev python3 -c "
from influxdb import InfluxDBClient
import os
client = InfluxDBClient(host='climacan-influxdb', port=int(os.getenv('INFLUXDB_PORT')))
client.switch_database('grafcan')
result = client.query('SHOW MEASUREMENTS LIMIT 1')
measurements = list(result.get_points())
if measurements:
    meas = measurements[0]['name']
    result = client.query(f'SELECT * FROM \"{meas}\" ORDER BY time DESC LIMIT 1')
    for point in result.get_points():
        print(f'Último dato en {meas}: {point.get(\"time\")}')"
```

## Resiliencia Implementada

### Mejoras en el Sistema

1. **Try-Catch en todas las funciones de tareas**
   - Las excepciones no detendrán el scheduler
   - Errores se registran en logs

2. **Configuración de APScheduler**
   - `coalesce=True`: Combina trabajos atrasados
   - `max_instances=1`: Solo una instancia por trabajo
   - `misfire_grace_time`: Tolerancia para trabajos retrasados
     - AEMET: 3600 segundos (1 hora)
     - Grafcan: 600 segundos (10 minutos)

3. **Reinicio Automático en run.sh**
   - Si un proceso falla, se reinicia automáticamente después de 30 segundos
   - Monitor cada 5 minutos verifica que los procesos estén vivos
   - Reinicio automático si algún proceso se detiene

4. **Logging Mejorado**
   - Todos los errores se registran con stack traces
   - Mensajes informativos sobre el estado del scheduler
   - Logs con timestamp para debugging

## Solución de Problemas

### Si los datos no se actualizan:

1. **Verificar que los contenedores estén corriendo**
   ```bash
   docker ps | grep climacan-dev
   ```

2. **Ver logs recientes**
   ```bash
   docker logs climacan-dev --tail=100
   ```

3. **Ejecutar script manualmente**
   ```bash
   # Para AEMET observaciones
   docker exec climacan-dev python3 src/aemet/files/get_conventional_observations.py

   # Para AEMET predicciones
   docker exec climacan-dev python3 src/aemet/files/get_canary_predictions.py

   # Para Grafcan
   docker exec climacan-dev python3 src/grafcan/files/write_last_observations.py
   ```

4. **Reiniciar el contenedor principal**
   ```bash
   cd /home/microgrid_itc/GitHub/ClimaCan/docker
   docker restart climacan-dev
   ```

### Verificar Estado de las APIs

```bash
# Verificar API AEMET
docker exec climacan-dev python3 -c "
import os, requests
token = os.getenv('AEMET_TOKEN')
url = 'https://opendata.aemet.es/opendata/api/observacion/convencional/todas'
r = requests.get(url, headers={'api_key': token})
print(f'AEMET Status: {r.status_code}')"

# Verificar API Grafcan
docker exec climacan-dev python3 -c "
import os, requests
token = os.getenv('GRAFCAN_TOKEN')
url = 'https://opendata.grafcan.es/proxy/datostiemporeal/HistEstEmaData'
r = requests.get(url, headers={'Authorization': f'Bearer {token}'})
print(f'Grafcan Status: {r.status_code}')"
```

## Horarios de Ejecución

### AEMET
- **Actualizar municipios**: Lunes a las 00:00 (días 1, 8, 15, 21)
- **Predicciones**: Cada 6 horas (00:00, 06:00, 12:00, 18:00)
- **Observaciones convencionales**: Cada hora (minuto 02)

### Grafcan
- **Actualizar estaciones**: Lunes, Miércoles, Viernes a las 23:00
- **Observaciones**: Cada 10 minutos
