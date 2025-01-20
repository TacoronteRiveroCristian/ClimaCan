#!/bin/bash

# Rutas absolutas o relativas a los scripts
SCRIPT_AEMET="src/aemet/main_aemet.py"
SCRIPT_GRAFCAN="src/grafcan/main_grafcan.py"

# Ejecutar los scripts en segundo plano
echo "Iniciando script AEMET..."
python3 "$SCRIPT_AEMET" 2>&1 &

echo "Iniciando script Grafcan..."
python3 "$SCRIPT_GRAFCAN" 2>&1 &

# Obtener los PIDs de los procesos en segundo plano
PID_AEMET=$!
PID_GRAFCAN=$!

echo "Script AEMET ejecutándose con PID $PID_AEMET"
echo "Script Grafcan ejecutándose con PID $PID_GRAFCAN"

# Mantener el script en ejecucion para que los procesos secundarios
# no se detengan y tampoco finalice el contenedor
while true; do
    sleep 3600
done
