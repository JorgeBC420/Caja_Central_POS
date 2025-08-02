#!/bin/bash
# Utilidades Docker para Caja Central POS

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Funciones de utilidad
log() { echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"; }
success() { echo -e "${GREEN}✓${NC} $1"; }
warning() { echo -e "${YELLOW}⚠${NC} $1"; }
error() { echo -e "${RED}✗${NC} $1"; }

show_help() {
    echo "Utilidades Docker - Caja Central POS"
    echo
    echo "Uso: $0 [COMANDO]"
    echo
    echo "Comandos disponibles:"
    echo "  start           Iniciar todos los servicios"
    echo "  stop            Detener todos los servicios"
    echo "  restart         Reiniciar todos los servicios"
    echo "  status          Mostrar estado de servicios"
    echo "  logs            Mostrar logs de todos los servicios"
    echo "  logs [SERVICE]  Mostrar logs de un servicio específico"
    echo "  backup          Crear backup manual"
    echo "  restore [FILE]  Restaurar desde backup"
    echo "  update          Actualizar imágenes y reiniciar"
    echo "  cleanup         Limpiar imágenes y contenedores no usados"
    echo "  health          Verificar salud de servicios"
    echo "  shell [SERVICE] Abrir shell en contenedor"
    echo "  db-shell        Abrir shell de base de datos"
    echo "  ssl-renew       Renovar certificados SSL"
    echo "  monitor         Monitor en tiempo real"
    echo "  reset           Reiniciar completamente (CUIDADO: borra datos)"
    echo
    echo "Ejemplos:"
    echo "  $0 start"
    echo "  $0 logs pos-app"
    echo "  $0 shell pos-app"
    echo "  $0 backup"
}

start_services() {
    log "Iniciando servicios de Caja Central POS..."
    
    # Verificar archivos necesarios
    if [ ! -f "docker-compose.yml" ]; then
        error "docker-compose.yml no encontrado"
        exit 1
    fi
    
    # Crear directorios si no existen
    mkdir -p data logs config certificates backups
    
    # Iniciar servicios en orden
    docker-compose up -d pos-database
    sleep 5
    docker-compose up -d pos-app pos-billing-api
    sleep 10
    docker-compose up -d pos-nginx pos-backup pos-monitor
    
    success "Servicios iniciados"
    show_status
}

stop_services() {
    log "Deteniendo servicios..."
    docker-compose down
    success "Servicios detenidos"
}

restart_services() {
    log "Reiniciando servicios..."
    docker-compose restart
    success "Servicios reiniciados"
    show_status
}

show_status() {
    log "Estado de servicios:"
    docker-compose ps
    echo
    
    # Verificar conectividad
    if curl -s -o /dev/null -w "%{http_code}" https://localhost | grep -q "200\|302"; then
        success "Sistema accesible en https://localhost"
    else
        warning "Sistema no responde en https://localhost"
    fi
}

show_logs() {
    local service=$1
    
    if [ -z "$service" ]; then
        log "Mostrando logs de todos los servicios..."
        docker-compose logs -f --tail=50
    else
        log "Mostrando logs de $service..."
        docker-compose logs -f --tail=50 "$service"
    fi
}

create_backup() {
    log "Creando backup manual..."
    
    # Ejecutar script de backup en contenedor
    docker-compose exec pos-backup /backup.sh
    
    # Mostrar backups disponibles
    echo
    log "Backups disponibles:"
    ls -lah backups/ | grep backup_
    
    success "Backup creado"
}

restore_backup() {
    local backup_file=$1
    
    if [ -z "$backup_file" ]; then
        error "Especifica el archivo de backup"
        echo "Backups disponibles:"
        ls -1 backups/ | grep backup_
        exit 1
    fi
    
    if [ ! -f "backups/$backup_file" ]; then
        error "Archivo de backup no encontrado: $backup_file"
        exit 1
    fi
    
    warning "Esta operación reemplazará los datos actuales"
    read -p "¿Continuar? (y/N): " confirm
    
    if [[ $confirm =~ ^[Yy]$ ]]; then
        log "Restaurando desde $backup_file..."
        
        # Detener servicios
        docker-compose stop pos-app pos-billing-api
        
        # Restaurar base de datos
        cp "backups/$backup_file" "data/caja_registradora_pos_cr.db"
        
        # Reiniciar servicios
        docker-compose start pos-app pos-billing-api
        
        success "Restauración completada"
    else
        log "Restauración cancelada"
    fi
}

update_system() {
    log "Actualizando sistema..."
    
    # Pull de nuevas imágenes
    docker-compose pull
    
    # Rebuild de imágenes locales
    docker-compose build --pull --no-cache
    
    # Reiniciar con nuevas imágenes
    docker-compose up -d
    
    success "Sistema actualizado"
    show_status
}

cleanup_docker() {
    log "Limpiando Docker..."
    
    # Limpiar contenedores parados
    docker container prune -f
    
    # Limpiar imágenes no utilizadas
    docker image prune -f
    
    # Limpiar volúmenes no utilizados
    docker volume prune -f
    
    # Limpiar redes no utilizadas
    docker network prune -f
    
    success "Limpieza completada"
}

check_health() {
    log "Verificando salud de servicios..."
    
    services=("pos-app" "pos-database" "pos-billing-api" "pos-nginx")
    all_healthy=true
    
    for service in "${services[@]}"; do
        if docker-compose ps "$service" | grep -q "Up"; then
            success "$service: Saludable"
        else
            error "$service: Con problemas"
            all_healthy=false
        fi
    done
    
    # Test de conectividad
    if curl -s -o /dev/null https://localhost; then
        success "Conectividad web: OK"
    else
        error "Conectividad web: FALLO"
        all_healthy=false
    fi
    
    if [ "$all_healthy" = true ]; then
        success "Todos los servicios están saludables"
    else
        warning "Algunos servicios tienen problemas"
        return 1
    fi
}

open_shell() {
    local service=$1
    
    if [ -z "$service" ]; then
        service="pos-app"
    fi
    
    log "Abriendo shell en $service..."
    docker-compose exec "$service" /bin/bash
}

open_db_shell() {
    log "Abriendo shell de base de datos..."
    docker-compose exec pos-database sqlite3 /data/caja_registradora_pos_cr.db
}

renew_ssl() {
    log "Renovando certificados SSL..."
    
    # Generar nuevos certificados
    openssl req -x509 -newkey rsa:4096 -keyout certificates/key.pem.new -out certificates/cert.pem.new -days 365 -nodes \
        -subj "/C=CR/ST=San Jose/L=San Jose/O=Caja Central POS/CN=localhost"
    
    # Backup de certificados actuales
    cp certificates/cert.pem certificates/cert.pem.backup
    cp certificates/key.pem certificates/key.pem.backup
    
    # Reemplazar certificados
    mv certificates/cert.pem.new certificates/cert.pem
    mv certificates/key.pem.new certificates/key.pem
    
    # Ajustar permisos
    chmod 600 certificates/key.pem certificates/cert.pem
    
    # Reiniciar nginx
    docker-compose restart pos-nginx
    
    success "Certificados SSL renovados"
}

monitor_system() {
    log "Iniciando monitor en tiempo real..."
    echo "Presiona Ctrl+C para salir"
    
    while true; do
        clear
        echo "=== MONITOR CAJA CENTRAL POS - $(date) ==="
        echo
        
        # Estado de servicios
        echo "📊 Estado de Servicios:"
        docker-compose ps
        echo
        
        # Uso de recursos
        echo "💻 Uso de Recursos:"
        docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
        echo
        
        # Logs recientes
        echo "📝 Logs Recientes:"
        docker-compose logs --tail=5 --since=1m
        echo
        
        sleep 30
    done
}

reset_system() {
    warning "PELIGRO: Esta operación eliminará TODOS los datos"
    warning "Esto incluye: base de datos, logs, configuración, certificados"
    echo
    
    read -p "Escribe 'CONFIRMAR' para continuar: " confirm
    
    if [ "$confirm" != "CONFIRMAR" ]; then
        log "Operación cancelada"
        exit 0
    fi
    
    log "Deteniendo servicios..."
    docker-compose down -v
    
    log "Eliminando datos..."
    rm -rf data/* logs/* backups/*
    
    log "Eliminando imágenes..."
    docker-compose down --rmi all
    
    log "Recreando sistema..."
    mkdir -p data logs config certificates backups
    
    success "Sistema reiniciado completamente"
    warning "Ejecuta '$0 start' para inicializar nuevamente"
}

# Función principal
main() {
    case "$1" in
        "start")
            start_services
            ;;
        "stop")
            stop_services
            ;;
        "restart")
            restart_services
            ;;
        "status")
            show_status
            ;;
        "logs")
            show_logs "$2"
            ;;
        "backup")
            create_backup
            ;;
        "restore")
            restore_backup "$2"
            ;;
        "update")
            update_system
            ;;
        "cleanup")
            cleanup_docker
            ;;
        "health")
            check_health
            ;;
        "shell")
            open_shell "$2"
            ;;
        "db-shell")
            open_db_shell
            ;;
        "ssl-renew")
            renew_ssl
            ;;
        "monitor")
            monitor_system
            ;;
        "reset")
            reset_system
            ;;
        *)
            show_help
            ;;
    esac
}

# Ejecutar comando
main "$@"
