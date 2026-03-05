#!/bin/bash

# Rutas absolutas o relativas a los scripts
SCRIPT_AEMET="src/aemet/main_aemet.py"
SCRIPT_GRAFCAN="src/grafcan/main_grafcan.py"

# Configuracion de reintentos
MAX_CONSECUTIVE_FAILURES=5
INITIAL_RESTART_DELAY=30
MAX_RESTART_DELAY=300

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Funcion para iniciar un script con reintentos limitados y backoff exponencial
start_with_retry() {
    local script=$1
    local name=$2
    local consecutive_failures=0
    local restart_delay=$INITIAL_RESTART_DELAY

    while [ $consecutive_failures -lt $MAX_CONSECUTIVE_FAILURES ]; do
        log "Iniciando $name..."
        python3 "$script" 2>&1
        exit_code=$?

        if [ $exit_code -eq 0 ]; then
            log "$name terminó normalmente."
            consecutive_failures=0
            restart_delay=$INITIAL_RESTART_DELAY
            break
        else
            consecutive_failures=$((consecutive_failures + 1))
            log "ERROR: $name falló con código $exit_code (fallo $consecutive_failures/$MAX_CONSECUTIVE_FAILURES)"

            if [ $consecutive_failures -ge $MAX_CONSECUTIVE_FAILURES ]; then
                log "CRITICO: $name alcanzó el máximo de fallos consecutivos ($MAX_CONSECUTIVE_FAILURES). Deteniendo reintentos."
                break
            fi

            log "Reiniciando $name en ${restart_delay} segundos (backoff exponencial)..."
            sleep $restart_delay
            # Backoff exponencial: 30s, 60s, 120s, 240s (con tope de MAX_RESTART_DELAY)
            restart_delay=$((restart_delay * 2))
            if [ $restart_delay -gt $MAX_RESTART_DELAY ]; then
                restart_delay=$MAX_RESTART_DELAY
            fi
        fi
    done

    return $consecutive_failures
}

# Ejecutar los scripts en segundo plano con reintentos limitados
start_with_retry "$SCRIPT_AEMET" "AEMET" &
PID_AEMET=$!

start_with_retry "$SCRIPT_GRAFCAN" "Grafcan" &
PID_GRAFCAN=$!

log "Script AEMET ejecutándose con PID $PID_AEMET"
log "Script Grafcan ejecutándose con PID $PID_GRAFCAN"

# Esperar a que ambos procesos terminen.
# No se usa monitor_processes para evitar acumulacion de procesos zombie.
# Docker restart: unless-stopped se encarga de reiniciar el contenedor si ambos terminan.

# Mantener el script en ejecución
wait
