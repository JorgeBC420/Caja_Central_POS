#!/bin/bash
# Script de backup automatizado para Caja Central POS

set -e  # Exit on any error

# Configuración
BACKUP_DIR="/backups"
DATA_DIR="/data"
LOGS_DIR="/logs"
DATE=$(date +"%Y%m%d_%H%M%S")
RETENTION_DAYS=${RETENTION_DAYS:-30}

# Función de logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Crear directorio de backup si no existe
mkdir -p "$BACKUP_DIR"

log "Iniciando backup automático..."

# Backup de base de datos
if [ -f "$DATA_DIR/caja_registradora_pos_cr.db" ]; then
    log "Respaldando base de datos principal..."
    cp "$DATA_DIR/caja_registradora_pos_cr.db" "$BACKUP_DIR/db_backup_$DATE.db"
    
    # Verificar integridad
    if sqlite3 "$BACKUP_DIR/db_backup_$DATE.db" "PRAGMA integrity_check;" | grep -q "ok"; then
        log "✓ Backup de BD principal completado y verificado"
    else
        log "✗ Error en integridad del backup de BD principal"
        exit 1
    fi
fi

# Backup de base de datos multi-tienda
if [ -f "$DATA_DIR/multistore_data.db" ]; then
    log "Respaldando base de datos multi-tienda..."
    cp "$DATA_DIR/multistore_data.db" "$BACKUP_DIR/multistore_backup_$DATE.db"
    log "✓ Backup de BD multi-tienda completado"
fi

# Backup de base de datos de restaurante
if [ -f "$DATA_DIR/restaurant.db" ]; then
    log "Respaldando base de datos de restaurante..."
    cp "$DATA_DIR/restaurant.db" "$BACKUP_DIR/restaurant_backup_$DATE.db"
    log "✓ Backup de BD restaurante completado"
fi

# Backup de historial de ventas
if [ -f "$DATA_DIR/sales_history.db" ]; then
    log "Respaldando historial de ventas..."
    cp "$DATA_DIR/sales_history.db" "$BACKUP_DIR/sales_backup_$DATE.db"
    log "✓ Backup de historial de ventas completado"
fi

# Backup de configuración
if [ -d "/app/config" ]; then
    log "Respaldando configuración..."
    tar -czf "$BACKUP_DIR/config_backup_$DATE.tar.gz" -C /app config/
    log "✓ Backup de configuración completado"
fi

# Backup de logs recientes (últimos 7 días)
if [ -d "$LOGS_DIR" ]; then
    log "Respaldando logs recientes..."
    find "$LOGS_DIR" -name "*.log" -mtime -7 -exec tar -czf "$BACKUP_DIR/logs_backup_$DATE.tar.gz" {} +
    log "✓ Backup de logs completado"
fi

# Crear archivo de metadatos del backup
cat > "$BACKUP_DIR/backup_metadata_$DATE.json" << EOF
{
    "backup_date": "$DATE",
    "backup_type": "automated",
    "files_backed_up": [
EOF

# Listar archivos respaldados
FIRST=true
for file in "$BACKUP_DIR"/*_$DATE.*; do
    if [ -f "$file" ]; then
        if [ "$FIRST" = true ]; then
            FIRST=false
        else
            echo "," >> "$BACKUP_DIR/backup_metadata_$DATE.json"
        fi
        echo "        \"$(basename "$file")\"" >> "$BACKUP_DIR/backup_metadata_$DATE.json"
    fi
done

cat >> "$BACKUP_DIR/backup_metadata_$DATE.json" << EOF
    ],
    "retention_days": $RETENTION_DAYS,
    "system_info": {
        "hostname": "$(hostname)",
        "disk_usage": "$(df -h $BACKUP_DIR | tail -1 | awk '{print $5}')"
    }
}
EOF

log "✓ Metadatos del backup generados"

# Limpiar backups antiguos
log "Limpiando backups antiguos (más de $RETENTION_DAYS días)..."
find "$BACKUP_DIR" -name "*backup_*" -mtime +$RETENTION_DAYS -delete
DELETED_COUNT=$(find "$BACKUP_DIR" -name "*backup_*" -mtime +$RETENTION_DAYS | wc -l)
log "✓ $DELETED_COUNT archivos antiguos eliminados"

# Verificar espacio en disco
DISK_USAGE=$(df "$BACKUP_DIR" | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 85 ]; then
    log "⚠️  Advertencia: Uso de disco alto ($DISK_USAGE%)"
fi

# Resumen del backup
TOTAL_FILES=$(ls -1 "$BACKUP_DIR"/*_$DATE.* 2>/dev/null | wc -l)
TOTAL_SIZE=$(du -sh "$BACKUP_DIR"/*_$DATE.* 2>/dev/null | awk '{total+=$1} END {print total "K"}')

log "=== RESUMEN DEL BACKUP ==="
log "Fecha: $DATE"
log "Archivos respaldados: $TOTAL_FILES"
log "Tamaño total: $TOTAL_SIZE"
log "Ubicación: $BACKUP_DIR"
log "=========================="

log "Backup automático completado exitosamente"

# Notificar éxito (opcional - implementar según necesidades)
# curl -X POST "http://pos-monitor:8080/backup-success" -d "backup_date=$DATE&files=$TOTAL_FILES"

exit 0
