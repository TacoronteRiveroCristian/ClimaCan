#!/bin/bash

# Rutas absolutas o relativas a los scripts
SCRIPT_AEMET="src/aemet/main_aemet.py"
SCRIPT_GRAFCAN="src/grafcan/main_grafcan.py"

# Función para iniciar un script con reintentos automáticos
start_with_retry() {
    local script=$1
    local name=$2
    local restart_delay=30

    while true; do
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Iniciando $name..."
        python3 "$script" 2>&1
        exit_code=$?

        if [ $exit_code -eq 0 ]; then
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] $name terminó normalmente"
            break
        else
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $name falló con código $exit_code"
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] Reiniciando $name en ${restart_delay} segundos..."
            sleep $restart_delay
        fi
    done
}

# Ejecutar los scripts en segundo plano con reintentos automáticos
start_with_retry "$SCRIPT_AEMET" "AEMET" &
PID_AEMET=$!

start_with_retry "$SCRIPT_GRAFCAN" "Grafcan" &
PID_GRAFCAN=$!

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Script AEMET ejecutándose con PID $PID_AEMET"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Script Grafcan ejecutándose con PID $PID_GRAFCAN"

# Función de monitoreo para verificar que los procesos sigan vivos
monitor_processes() {
    while true; do
        sleep 300  # Verificar cada 5 minutos

        if ! ps -p $PID_AEMET > /dev/null 2>&1; then
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] ADVERTENCIA: Proceso AEMET no está corriendo. Reiniciando..."
            start_with_retry "$SCRIPT_AEMET" "AEMET" &
            PID_AEMET=$!
        fi

        if ! ps -p $PID_GRAFCAN > /dev/null 2>&1; then
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] ADVERTENCIA: Proceso Grafcan no está corriendo. Reiniciando..."
            start_with_retry "$SCRIPT_GRAFCAN" "Grafcan" &
            PID_GRAFCAN=$!
        fi
    done
}

# Iniciar el monitor en segundo plano
monitor_processes &

# Mantener el script en ejecución
wait
