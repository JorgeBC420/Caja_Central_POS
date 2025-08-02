# Native Deployment Script - Caja Central POS
# PowerShell script para despliegue nativo sin Docker

param([switch]$Force)

Write-Host "=== DESPLIEGUE NATIVO - CAJA CENTRAL POS ===" -ForegroundColor Green
Write-Host ""

# Check Python
try {
    $pythonVersion = python --version
    Write-Host "Python encontrado: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Error: Python no encontrado" -ForegroundColor Red
    exit 1
}

# Create directories
Write-Host "Creando directorios..." -ForegroundColor Cyan
$dirs = @("data", "logs", "config", "backups", "temp")
foreach ($dir in $dirs) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "  + $dir" -ForegroundColor Green
    } else {
        Write-Host "  - $dir (ya existe)" -ForegroundColor Yellow
    }
}

# Initialize database
Write-Host "Inicializando base de datos..." -ForegroundColor Cyan
$dbPath = "data\caja_registradora_pos_cr.db"
if (!(Test-Path $dbPath)) {
    New-Item -ItemType File -Path $dbPath -Force | Out-Null
    Write-Host "  + Base de datos creada" -ForegroundColor Green
} else {
    Write-Host "  - Base de datos existe" -ForegroundColor Yellow
}

# Check requirements.txt
if (Test-Path "requirements.txt") {
    Write-Host "Instalando dependencias..." -ForegroundColor Cyan
    try {
        python -m pip install -r requirements.txt --user
        Write-Host "  + Dependencias instaladas" -ForegroundColor Green
    } catch {
        Write-Host "  ! Error instalando dependencias" -ForegroundColor Yellow
        Write-Host "  Continuando sin instalacion..." -ForegroundColor Yellow
    }
} else {
    Write-Host "  ! requirements.txt no encontrado" -ForegroundColor Yellow
}

# Check main application files
$mainFiles = @("main.py", "app.py", "pos_modern.py", "main_system.py")
$mainFile = $null

foreach ($file in $mainFiles) {
    if (Test-Path $file) {
        $mainFile = $file
        Write-Host "Archivo principal encontrado: $file" -ForegroundColor Green
        break
    }
}

if (!$mainFile) {
    Write-Host "Error: No se encontro archivo principal de aplicacion" -ForegroundColor Red
    Write-Host "Archivos buscados: $($mainFiles -join ', ')" -ForegroundColor Yellow
    exit 1
}

# Create startup script
$startupScript = @"
@echo off
echo Iniciando Caja Central POS...
cd /d "%~dp0"
python $mainFile
pause
"@

$startupScript | Out-File -FilePath "start-app.bat" -Encoding ASCII
Write-Host "Script de inicio creado: start-app.bat" -ForegroundColor Green

# Create config file if needed
if (!(Test-Path "config\app.ini")) {
    $configContent = @"
[DATABASE]
path=data/caja_registradora_pos_cr.db
backup_interval=3600

[LOGGING]
level=INFO
file=logs/app.log

[SECURITY]
session_timeout=1800
max_login_attempts=3

[UI]
theme=modern
language=es
"@
    $configContent | Out-File -FilePath "config\app.ini" -Encoding ASCII
    Write-Host "Configuracion basica creada" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== DESPLIEGUE COMPLETADO ===" -ForegroundColor Green
Write-Host ""
Write-Host "Opciones de inicio:" -ForegroundColor Cyan
Write-Host "  1. Doble clic en: start-app.bat" -ForegroundColor White
Write-Host "  2. PowerShell: python $mainFile" -ForegroundColor White
Write-Host "  3. CMD: python $mainFile" -ForegroundColor White
Write-Host ""
Write-Host "Ubicacion de datos:" -ForegroundColor Cyan
Write-Host "  Base de datos: .\data\" -ForegroundColor White
Write-Host "  Logs: .\logs\" -ForegroundColor White
Write-Host "  Configuracion: .\config\" -ForegroundColor White
Write-Host "  Backups: .\backups\" -ForegroundColor White
Write-Host ""

# Ask if user wants to start the application
$response = Read-Host "Deseas iniciar la aplicacion ahora? (s/n)"
if ($response -eq "s" -or $response -eq "S") {
    Write-Host "Iniciando aplicacion..." -ForegroundColor Green
    Start-Process python -ArgumentList $mainFile -NoNewWindow
} else {
    Write-Host "Usa 'python $mainFile' para iniciar cuando estes listo" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Sistema POS listo para usar!" -ForegroundColor Green
