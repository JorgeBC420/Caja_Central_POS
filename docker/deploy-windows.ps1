# Script de despliegue para Windows - Caja Central POS
# PowerShell script para implementacion Docker en Windows

param(
    [switch]$Help,
    [switch]$Force
)

function Write-Log {
    param([string]$Message, [string]$Color = "Cyan")
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] $Message" -ForegroundColor $Color
}

function Write-Success {
    param([string]$Message)
    Write-Host "+ $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "! $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "X $Message" -ForegroundColor Red
}

function Show-Help {
    Write-Host "=== Despliegue Docker - Caja Central POS ===" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Uso: .\docker\deploy-windows.ps1 [-Help] [-Force]"
    Write-Host ""
    Write-Host "Parametros:"
    Write-Host "  -Help   : Muestra esta ayuda"
    Write-Host "  -Force  : Fuerza la reinstalacion completa"
    Write-Host ""
    Write-Host "Ejemplo:"
    Write-Host "  .\docker\deploy-windows.ps1"
    Write-Host "  .\docker\deploy-windows.ps1 -Force"
}

function Test-Prerequisites {
    Write-Log "Verificando prerequisitos..."
    
    # Verificar Docker
    try {
        $dockerVersion = docker --version
        Write-Success "Docker encontrado: $dockerVersion"
    }
    catch {
        Write-Error "Docker no esta instalado o no esta en el PATH"
        Write-Host "Instala Docker Desktop desde: https://www.docker.com/products/docker-desktop/"
        exit 1
    }
    
    # Verificar Docker Compose
    try {
        $composeVersion = docker-compose --version
        Write-Success "Docker Compose encontrado: $composeVersion"
    }
    catch {
        Write-Error "Docker Compose no esta disponible"
        exit 1
    }
    
    # Verificar que Docker este corriendo
    try {
        docker info | Out-Null
        Write-Success "Docker daemon esta corriendo"
    }
    catch {
        Write-Error "Docker daemon no esta corriendo. Inicia Docker Desktop"
        exit 1
    }
}

function New-Directories {
    Write-Log "Creando estructura de directorios..."
    
    $directories = @("data", "logs", "config", "certificates", "backups")
    
    foreach ($dir in $directories) {
        if (!(Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            Write-Success "Directorio creado: $dir"
        } else {
            Write-Success "Directorio ya existe: $dir"
        }
    }
}

function New-SSLCertificates {
    Write-Log "Configurando certificados SSL..."
    
    $certPath = "certificates\cert.pem"
    $keyPath = "certificates\key.pem"
    
    if (!(Test-Path $certPath) -or !(Test-Path $keyPath) -or $Force) {
        Write-Warning "Creando certificados de desarrollo..."
        
        # Crear archivos placeholder para desarrollo
        "# Certificado SSL de desarrollo - Caja Central POS" | Out-File -FilePath $certPath -Encoding UTF8
        "# Para producción, reemplaza con certificado real" | Add-Content -Path $certPath -Encoding UTF8
        
        "# Clave privada SSL de desarrollo - Caja Central POS" | Out-File -FilePath $keyPath -Encoding UTF8
        "# Para producción, reemplaza con clave privada real" | Add-Content -Path $keyPath -Encoding UTF8
        
        Write-Success "Certificados de desarrollo creados"
        Write-Warning "IMPORTANTE: Para producción, genera certificados SSL reales"
    } else {
        Write-Success "Certificados SSL ya existen"
    }
}

function Set-Environment {
    Write-Log "Configurando variables de entorno..."
    
    if (!(Test-Path ".env") -or $Force) {
        $envContent = @"
# Configuración Docker - Caja Central POS
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
"@
        $envContent | Out-File -FilePath ".env" -Encoding UTF8
        Write-Success "Archivo .env creado"
    } else {
        Write-Success "Archivo .env ya existe"
    }
}

function Test-DockerConfig {
    Write-Log "Validando configuración Docker..."
    
    if (!(Test-Path "docker-compose.yml")) {
        Write-Error "Archivo docker-compose.yml no encontrado"
        return $false
    }
    
    try {
        docker-compose config | Out-Null
        Write-Success "Configuración Docker válida"
        return $true
    }
    catch {
        Write-Error "Error en configuración Docker Compose"
        Write-Host $_.Exception.Message -ForegroundColor Red
        return $false
    }
}

function Initialize-Database {
    Write-Log "Inicializando base de datos..."
    
    $dbPath = "data\caja_registradora_pos_cr.db"
    if (!(Test-Path $dbPath)) {
        # Crear archivo de base de datos vacío
        New-Item -ItemType File -Path $dbPath -Force | Out-Null
        Write-Success "Base de datos inicializada"
    } else {
        Write-Success "Base de datos ya existe"
    }
}

function Start-Services {
    Write-Log "Desplegando servicios Docker..."
    
    # Detener servicios existentes
    Write-Log "Deteniendo servicios existentes..."
    try {
        docker-compose down 2>$null
    }
    catch {
        Write-Warning "No hay servicios corriendo para detener"
    }
    
    # Verificar si hay imágenes para construir
    if (Test-Path "Dockerfile") {
        Write-Log "Construyendo imágenes Docker..."
        try {
            docker-compose build --no-cache
            Write-Success "Imágenes construidas"
        }
        catch {
            Write-Warning "Error construyendo imágenes, continuando con imágenes existentes..."
        }
    }
    
    # Iniciar servicios
    Write-Log "Iniciando servicios..."
    try {
        docker-compose up -d
        Write-Success "Servicios iniciados"
        return $true
    }
    catch {
        Write-Error "Error iniciando servicios: $($_.Exception.Message)"
        return $false
    }
}

function Test-ServiceHealth {
    Write-Log "Verificando salud de servicios..."
    
    # Esperar a que los servicios se inicien
    Write-Log "Esperando inicialización de servicios..."
    Start-Sleep -Seconds 15
    
    # Verificar servicios con docker-compose
    try {
        $services = docker-compose ps --services
        $runningServices = 0
        
        foreach ($service in $services) {
            $status = docker-compose ps $service
            if ($status -match "Up") {
                Write-Success "$service está ejecutándose"
                $runningServices++
            } else {
                Write-Warning "$service no está ejecutándose"
            }
        }
        
        return $runningServices -gt 0
    }
    catch {
        Write-Warning "No se pudo verificar el estado de los servicios"
        return $false
    }
}

function Show-DeploymentInfo {
    Write-Host ""
    Write-Host "=== DESPLIEGUE COMPLETADO ===" -ForegroundColor Green
    Write-Host ""
    Write-Host "🌐 URLs de acceso:" -ForegroundColor Cyan
    Write-Host "   Aplicación:      http://localhost:8080"
    Write-Host "   API:            http://localhost:8000"
    Write-Host ""
    Write-Host "📊 Estado de servicios:" -ForegroundColor Cyan
    try {
        docker-compose ps
    }
    catch {
        Write-Warning "No se pudo mostrar el estado de los servicios"
    }
    Write-Host ""
    Write-Host "📋 Comandos útiles:" -ForegroundColor Cyan
    Write-Host "   Ver logs:        docker-compose logs -f"
    Write-Host "   Reiniciar:       docker-compose restart"
    Write-Host "   Detener:         docker-compose down"
    Write-Host "   Estado:          docker-compose ps"
    Write-Host ""
    Write-Host "💾 Ubicación de datos:" -ForegroundColor Cyan
    Write-Host "   Base de datos:   .\data\"
    Write-Host "   Logs:           .\logs\"
    Write-Host "   Backups:        .\backups\"
    Write-Host ""
    Write-Success "¡Sistema POS configurado!"
}

# Función principal
function Main {
    if ($Help) {
        Show-Help
        return
    }
    
    Write-Host ""
    Write-Host "🚀 Despliegue Docker - Caja Central POS" -ForegroundColor Green
    Write-Host ""
    
    try {
        Test-Prerequisites
        New-Directories
        New-SSLCertificates
        Set-Environment
        
        if (!(Test-DockerConfig)) {
            Write-Error "Configuración Docker inválida"
            return
        }
        
        Initialize-Database
        
        if (Start-Services) {
            if (Test-ServiceHealth) {
                Show-DeploymentInfo
            } else {
                Write-Warning "Algunos servicios pueden tener problemas"
                Write-Host "Verifica los logs con: docker-compose logs" -ForegroundColor Yellow
            }
        } else {
            Write-Error "Fallo en el inicio de servicios"
        }
    }
    catch {
        Write-Error "Error durante el despliegue: $($_.Exception.Message)"
        Write-Host "Para más detalles ejecuta: docker-compose logs" -ForegroundColor Yellow
    }
}

# Ejecutar función principal
Main
