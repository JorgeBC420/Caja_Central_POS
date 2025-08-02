#!/bin/bash
# Script de despliegue seguro para Caja Central POS

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función de logging
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✓${NC} $1"
}

warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

error() {
    echo -e "${RED}✗${NC} $1"
}

# Verificar prerequisites
check_prerequisites() {
    log "Verificando prerequisites..."
    
    if ! command -v docker &> /dev/null; then
        error "Docker no está instalado"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose no está instalado"
        exit 1
    fi
    
    success "Prerequisites verificados"
}

# Crear directorios necesarios
create_directories() {
    log "Creando estructura de directorios..."
    
    mkdir -p data logs config certificates backups
    chmod 755 data logs backups
    chmod 700 config certificates
    
    success "Directorios creados"
}

# Generar certificados SSL auto-firmados (para desarrollo)
generate_certificates() {
    log "Generando certificados SSL..."
    
    if [ ! -f "certificates/cert.pem" ] || [ ! -f "certificates/key.pem" ]; then
        openssl req -x509 -newkey rsa:4096 -keyout certificates/key.pem -out certificates/cert.pem -days 365 -nodes \
            -subj "/C=CR/ST=San Jose/L=San Jose/O=Caja Central POS/CN=localhost"
        
        chmod 600 certificates/key.pem certificates/cert.pem
        success "Certificados SSL generados"
    else
        success "Certificados SSL ya existentes"
    fi
}

# Configurar variables de entorno
setup_environment() {
    log "Configurando variables de entorno..."
    
    if [ ! -f ".env" ]; then
        cp .env.docker .env
        success "Archivo .env creado desde plantilla"
    else
        success "Archivo .env ya existe"
    fi
}

# Validar configuración de seguridad
validate_security() {
    log "Validando configuración de seguridad..."
    
    # Verificar permisos de archivos sensibles
    if [ -f "certificates/key.pem" ]; then
        PERMS=$(stat -c "%a" certificates/key.pem)
        if [ "$PERMS" != "600" ]; then
            warning "Permisos de clave privada no son seguros, corrigiendo..."
            chmod 600 certificates/key.pem
        fi
    fi
    
    # Verificar que no hay contraseñas por defecto
    if grep -q "changeme\|password123\|admin" .env 2>/dev/null; then
        error "Se encontraron contraseñas por defecto en .env"
        exit 1
    fi
    
    success "Configuración de seguridad validada"
}

# Construir imágenes
build_images() {
    log "Construyendo imágenes Docker..."
    
    docker-compose build --no-cache --pull
    
    success "Imágenes construidas"
}

# Inicializar base de datos
init_database() {
    log "Inicializando base de datos..."
    
    if [ ! -f "data/caja_registradora_pos_cr.db" ]; then
        # Crear base de datos inicial
        touch data/caja_registradora_pos_cr.db
        chmod 600 data/caja_registradora_pos_cr.db
        success "Base de datos inicializada"
    else
        success "Base de datos ya existe"
    fi
}

# Verificar configuración Docker
verify_docker_config() {
    log "Verificando configuración Docker..."
    
    # Verificar docker-compose.yml
    if ! docker-compose config > /dev/null 2>&1; then
        error "Error en docker-compose.yml"
        exit 1
    fi
    
    success "Configuración Docker válida"
}

# Desplegar servicios
deploy_services() {
    log "Desplegando servicios..."
    
    # Detener servicios existentes
    docker-compose down
    
    # Iniciar servicios en orden
    docker-compose up -d pos-database
    sleep 5
    
    docker-compose up -d pos-app pos-billing-api
    sleep 10
    
    docker-compose up -d pos-nginx pos-backup pos-monitor
    
    success "Servicios desplegados"
}

# Verificar salud de servicios
check_health() {
    log "Verificando salud de servicios..."
    
    # Esperar a que los servicios estén listos
    sleep 30
    
    # Verificar cada servicio
    services=("pos-app" "pos-billing-api" "pos-nginx")
    
    for service in "${services[@]}"; do
        if docker-compose ps $service | grep -q "Up"; then
            success "$service está ejecutándose"
        else
            error "$service no está ejecutándose correctamente"
            docker-compose logs $service
            exit 1
        fi
    done
}

# Configurar monitoreo
setup_monitoring() {
    log "Configurando monitoreo..."
    
    # Crear script de monitoreo básico
    cat > monitor.sh << 'EOF'
#!/bin/bash
while true; do
    echo "[$(date)] Verificando servicios..."
    docker-compose ps
    echo "---"
    sleep 300  # 5 minutos
done
EOF
    
    chmod +x monitor.sh
    success "Monitoreo configurado"
}

# Mostrar información de despliegue
show_deployment_info() {
    log "=== INFORMACIÓN DE DESPLIEGUE ==="
    echo
    echo "🌐 URLs de acceso:"
    echo "   HTTPS: https://localhost"
    echo "   HTTP:  http://localhost (redirige a HTTPS)"
    echo "   App:   http://localhost:8080 (desarrollo)"
    echo
    echo "📊 Servicios desplegados:"
    docker-compose ps
    echo
    echo "📋 Comandos útiles:"
    echo "   Ver logs:        docker-compose logs -f"
    echo "   Reiniciar:       docker-compose restart"
    echo "   Detener:         docker-compose down"
    echo "   Estado:          docker-compose ps"
    echo
    echo "🔒 Certificados SSL:"
    echo "   Ubicación:       ./certificates/"
    echo "   Válidos hasta:   $(openssl x509 -enddate -noout -in certificates/cert.pem | cut -d= -f2)"
    echo
    echo "💾 Datos:"
    echo "   Base de datos:   ./data/"
    echo "   Logs:           ./logs/"
    echo "   Backups:        ./backups/"
    echo
    success "Despliegue completado exitosamente"
}

# Función principal
main() {
    echo
    log "🚀 Iniciando despliegue seguro de Caja Central POS"
    echo
    
    check_prerequisites
    create_directories
    generate_certificates
    setup_environment
    validate_security
    verify_docker_config
    build_images
    init_database
    deploy_services
    check_health
    setup_monitoring
    
    echo
    show_deployment_info
}

# Ejecutar función principal
main "$@"
