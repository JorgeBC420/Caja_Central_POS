# Script de despliegue para Windows - Caja Central POS
# PowerShell script para implementación Docker en Windows

param(
    [switch]$Help,
    [switch]$Force
)

# Configuración de colores para PowerShell
$Host.UI.RawUI.ForegroundColor = "White"

function Write-Log {
    param([string]$Message, [string]$Color = "Cyan")
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] $Message" -ForegroundColor $Color
}

function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠ $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

function Show-Help {
    Write-Host "=== Despliegue Docker - Caja Central POS ===" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Uso: .\docker\deploy.ps1 [-Help] [-Force]"
    Write-Host ""
    Write-Host "Parámetros:"
    Write-Host "  -Help   : Muestra esta ayuda"
    Write-Host "  -Force  : Fuerza la reinstalación completa"
    Write-Host ""
    Write-Host "Ejemplo:"
    Write-Host "  .\docker\deploy.ps1"
    Write-Host "  .\docker\deploy.ps1 -Force"
}

function Test-Prerequisites {
    Write-Log "Verificando prerequisitos..."
    
    # Verificar Docker
    try {
        $dockerVersion = docker --version
        Write-Success "Docker encontrado: $dockerVersion"
    }
    catch {
        Write-Error "Docker no está instalado o no está en el PATH"
        Write-Host "Instala Docker Desktop desde: https://www.docker.com/products/docker-desktop/"
        exit 1
    }
    
    # Verificar Docker Compose
    try {
        $composeVersion = docker-compose --version
        Write-Success "Docker Compose encontrado: $composeVersion"
    }
    catch {
        Write-Error "Docker Compose no está disponible"
        exit 1
    }
    
    # Verificar que Docker esté corriendo
    try {
        docker info | Out-Null
        Write-Success "Docker daemon está corriendo"
    }
    catch {
        Write-Error "Docker daemon no está corriendo. Inicia Docker Desktop"
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
    Write-Log "Generando certificados SSL..."
    
    $certPath = "certificates\cert.pem"
    $keyPath = "certificates\key.pem"
    
    if (!(Test-Path $certPath) -or !(Test-Path $keyPath) -or $Force) {
        # Verificar si OpenSSL está disponible
        try {
            openssl version | Out-Null
            
            # Generar certificados con OpenSSL
            openssl req -x509 -newkey rsa:4096 -keyout $keyPath -out $certPath -days 365 -nodes -subj "/C=CR/ST=San Jose/L=San Jose/O=Caja Central POS/CN=localhost"
            
            Write-Success "Certificados SSL generados con OpenSSL"
        }
        catch {
            Write-Warning "OpenSSL no encontrado, creando certificados de desarrollo..."
            
            # Crear certificados básicos para desarrollo
            @"
-----BEGIN CERTIFICATE-----
MIIDXTCCAkWgAwIBAgIJAKoK/heBjcOuMA0GCSqGSIb3DQEBBQUAMEUxCzAJBgNV
BAYTAkNSMRMwEQYDVQQIDApTYW4gSm9zZTEhMB8GA1UECgwYQ2FqYSBDZW50cmFs
IFBPU19UZXN0MB4XDTIwMDEwMTAwMDAwMFoXDTI1MTIzMTIzNTk1OVowRTELMAkG
A1UEBhMCQ1IxEzARBgNVBAgMClNhbiBKb3NlMSEwHwYDVQQKDBhDYWphIENlbnRy
YWwgUE9TX1Rlc3QwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQC1hTbx
...
-----END CERTIFICATE-----
"@ | Out-File -FilePath $certPath -Encoding ASCII
            
            @"
-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC1hTbxTest...
-----END PRIVATE KEY-----
"@ | Out-File -FilePath $keyPath -Encoding ASCII
            
            Write-Success "Certificados de desarrollo creados"
        }
    } else {
        Write-Success "Certificados SSL ya existen"
    }
}

function Set-Environment {
    Write-Log "Configurando variables de entorno..."
    
    if (!(Test-Path ".env")) {
        if (Test-Path ".env.docker") {
            Copy-Item ".env.docker" ".env"
            Write-Success "Archivo .env creado desde plantilla"
        } else {
            Write-Warning "Plantilla .env.docker no encontrada, creando configuración básica..."
            
            @"
# Configuración Docker - Caja Central POS
COMPOSE_PROJECT_NAME=cajacentral-pos
DATABASE_PATH=/app/data/caja_registradora_pos_cr.db
SSL_ENABLED=true
LOG_LEVEL=INFO
BACKUP_RETENTION_DAYS=30
TZ=America/Costa_Rica
"@ | Out-File -FilePath ".env" -Encoding UTF8
            
            Write-Success "Archivo .env básico creado"
        }
    } else {
        Write-Success "Archivo .env ya existe"
    }
}

function Test-DockerConfig {
    Write-Log "Validando configuración Docker..."
    
    try {
        docker-compose config | Out-Null
        Write-Success "Configuración Docker válida"
    }
    catch {
        Write-Error "Error en configuración Docker Compose"
        Write-Host "Revisa el archivo docker-compose.yml"
        exit 1
    }
}

function Start-Services {
    Write-Log "Desplegando servicios Docker..."
    
    # Detener servicios existentes si están corriendo
    Write-Log "Deteniendo servicios existentes..."
    docker-compose down 2>$null
    
    # Construir imágenes
    Write-Log "Construyendo imágenes Docker..."
    docker-compose build --no-cache --pull
    
    # Inicializar base de datos si no existe
    if (!(Test-Path "data\caja_registradora_pos_cr.db")) {
        Write-Log "Inicializando base de datos..."
        New-Item -ItemType File -Path "data\caja_registradora_pos_cr.db" -Force | Out-Null
    }
    
    # Iniciar servicios en orden
    Write-Log "Iniciando base de datos..."
    docker-compose up -d pos-database
    Start-Sleep -Seconds 5
    
    Write-Log "Iniciando aplicación y API..."
    docker-compose up -d pos-app pos-billing-api
    Start-Sleep -Seconds 10
    
    Write-Log "Iniciando servicios auxiliares..."
    docker-compose up -d pos-nginx pos-backup pos-monitor
    
    Write-Success "Servicios desplegados"
}

function Test-ServiceHealth {
    Write-Log "Verificando salud de servicios..."
    
    # Esperar a que los servicios estén listos
    Start-Sleep -Seconds 30
    
    # Verificar servicios
    $services = @("pos-app", "pos-database", "pos-nginx")
    $allHealthy = $true
    
    foreach ($service in $services) {
        $status = docker-compose ps $service
        if ($status -match "Up") {
            Write-Success "$service está ejecutándose"
        } else {
            Write-Error "$service no está ejecutándose correctamente"
            docker-compose logs $service
            $allHealthy = $false
        }
    }
    
    # Test de conectividad web (opcional, puede fallar en algunos entornos)
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8080" -TimeoutSec 5 -UseBasicParsing
        Write-Success "Aplicación web responde correctamente"
    }
    catch {
        Write-Warning "Aplicación web no responde aún (normal en primer inicio)"
    }
    
    return $allHealthy
}

function Show-DeploymentInfo {
    Write-Host ""
    Write-Host "=== DESPLIEGUE COMPLETADO ===" -ForegroundColor Green
    Write-Host ""
    Write-Host "🌐 URLs de acceso:" -ForegroundColor Cyan
    Write-Host "   HTTP Local:  http://localhost:8080"
    Write-Host "   HTTPS:       https://localhost (si nginx está configurado)"
    Write-Host ""
    Write-Host "📊 Estado de servicios:" -ForegroundColor Cyan
    docker-compose ps
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
    Write-Success "¡Sistema POS listo para usar!"
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
        Test-DockerConfig
        Start-Services
        
        if (Test-ServiceHealth) {
            Show-DeploymentInfo
        } else {
            Write-Warning "Algunos servicios tienen problemas. Revisa los logs con:"
            Write-Host "docker-compose logs" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Error "Error durante el despliegue: $($_.Exception.Message)"
        Write-Host "Ejecuta 'docker-compose logs' para más detalles" -ForegroundColor Yellow
        exit 1
    }
}

# Ejecutar función principal
Main
