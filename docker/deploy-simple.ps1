# Deploy Script for Windows - Caja Central POS
# Simple PowerShell deployment script

param([switch]$Force)

Write-Host "Iniciando despliegue Docker..." -ForegroundColor Green

# Check Docker
try {
    docker --version | Out-Null
    Write-Host "Docker OK" -ForegroundColor Green
} catch {
    Write-Host "Error: Docker no encontrado" -ForegroundColor Red
    exit 1
}

# Check Docker Compose
try {
    docker-compose --version | Out-Null
    Write-Host "Docker Compose OK" -ForegroundColor Green
} catch {
    Write-Host "Error: Docker Compose no encontrado" -ForegroundColor Red
    exit 1
}

# Create directories
$dirs = @("data", "logs", "config", "certificates", "backups")
foreach ($dir in $dirs) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "Directorio creado: $dir" -ForegroundColor Cyan
    }
}

# Create SSL certificates (development)
$certPath = "certificates\cert.pem"
$keyPath = "certificates\key.pem"

if (!(Test-Path $certPath) -or $Force) {
    "# Development SSL Certificate" | Out-File -FilePath $certPath -Encoding ASCII
    Write-Host "Certificado creado" -ForegroundColor Cyan
}

if (!(Test-Path $keyPath) -or $Force) {
    "# Development SSL Key" | Out-File -FilePath $keyPath -Encoding ASCII
    Write-Host "Clave SSL creada" -ForegroundColor Cyan
}

# Create .env file
if (!(Test-Path ".env") -or $Force) {
    @"
COMPOSE_PROJECT_NAME=cajacentral-pos
DATABASE_PATH=/app/data/caja_registradora_pos_cr.db
SSL_ENABLED=false
LOG_LEVEL=INFO
BACKUP_RETENTION_DAYS=30
TZ=America/Costa_Rica
HTTP_PORT=80
HTTPS_PORT=443
APP_PORT=8080
API_PORT=8000
"@ | Out-File -FilePath ".env" -Encoding ASCII
    Write-Host "Archivo .env creado" -ForegroundColor Cyan
}

# Initialize database
$dbPath = "data\caja_registradora_pos_cr.db"
if (!(Test-Path $dbPath)) {
    New-Item -ItemType File -Path $dbPath -Force | Out-Null
    Write-Host "Base de datos inicializada" -ForegroundColor Cyan
}

# Validate Docker Compose
try {
    docker-compose config | Out-Null
    Write-Host "Configuracion Docker valida" -ForegroundColor Green
} catch {
    Write-Host "Error en docker-compose.yml" -ForegroundColor Red
    exit 1
}

# Stop existing services
Write-Host "Deteniendo servicios existentes..." -ForegroundColor Yellow
docker-compose down 2>$null

# Start services
Write-Host "Iniciando servicios..." -ForegroundColor Yellow
try {
    docker-compose up -d
    Write-Host "Servicios iniciados correctamente" -ForegroundColor Green
    
    # Wait and check status
    Start-Sleep -Seconds 10
    Write-Host "Estado de servicios:" -ForegroundColor Cyan
    docker-compose ps
    
    Write-Host ""
    Write-Host "=== DESPLIEGUE COMPLETADO ===" -ForegroundColor Green
    Write-Host "Aplicacion: http://localhost:8080" -ForegroundColor Cyan
    Write-Host "API: http://localhost:8000" -ForegroundColor Cyan
    Write-Host "Logs: docker-compose logs -f" -ForegroundColor Yellow
    
} catch {
    Write-Host "Error iniciando servicios" -ForegroundColor Red
    Write-Host "Logs de error:" -ForegroundColor Yellow
    docker-compose logs
    exit 1
}
