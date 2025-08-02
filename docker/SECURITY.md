# Configuración de Seguridad Docker - Caja Central POS

## Hardening de Contenedores

### 1. Usuarios No-Root
```dockerfile
# Crear usuario específico para la aplicación
RUN groupadd -r posuser && useradd -r -g posuser posuser
USER posuser
```

### 2. Filesystem de Solo Lectura
```yaml
read_only: true
tmpfs:
  - /tmp:noexec,nosuid,size=100m
```

### 3. Capabilities Mínimas
```yaml
security_opt:
  - no-new-privileges:true
cap_drop:
  - ALL
cap_add:
  - NET_BIND_SERVICE  # Solo si necesita puertos < 1024
```

### 4. Límites de Recursos
```yaml
deploy:
  resources:
    limits:
      memory: 512M
      cpus: '1.0'
    reservations:
      memory: 256M
      cpus: '0.5'
```

## Seguridad de Red

### 1. Redes Internas
```yaml
networks:
  pos-internal:
    driver: bridge
    internal: true  # Sin acceso a internet
```

### 2. Políticas de Firewall
```bash
# Bloquear todo tráfico por defecto
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT DROP

# Permitir solo tráfico necesario
iptables -A INPUT -p tcp --dport 443 -j ACCEPT  # HTTPS
iptables -A INPUT -p tcp --dport 80 -j ACCEPT   # HTTP (redirect)
```

### 3. Rate Limiting
```nginx
limit_req_zone $binary_remote_addr zone=pos:10m rate=10r/s;
limit_req zone=pos burst=20 nodelay;
```

## Secretos y Configuración

### 1. Docker Secrets
```yaml
secrets:
  ssl_cert:
    file: ./certificates/cert.pem
  ssl_key:
    file: ./certificates/key.pem
  db_password:
    external: true
```

### 2. Variables de Entorno Seguras
```bash
# NO hacer esto
ENV DATABASE_PASSWORD=mypassword

# Hacer esto
ENV DATABASE_PASSWORD_FILE=/run/secrets/db_password
```

### 3. Gestión de Certificados
```bash
# Generar certificados con validez limitada
openssl req -x509 -newkey rsa:4096 -days 90 -nodes \
  -keyout key.pem -out cert.pem

# Rotación automática
0 0 1 * * /app/scripts/rotate-certs.sh
```

## Monitoreo y Logging

### 1. Logging Estructurado
```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
    labels: "service,environment"
```

### 2. Health Checks
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1
```

### 3. Métricas de Seguridad
```bash
# Monitor de intentos de login fallidos
docker logs pos-app | grep "LOGIN_FAILED" | wc -l

# Monitor de uso de recursos
docker stats --no-stream
```

## Backup y Recuperación

### 1. Backup Automatizado
```bash
#!/bin/bash
# Backup con encriptación
tar -czf - /data | gpg --cipher-algo AES256 --compress-algo 1 \
  --symmetric --output backup-$(date +%Y%m%d).tar.gz.gpg
```

### 2. Recuperación de Desastres
```bash
# Plan de recuperación en menos de 15 minutos
1. Restaurar desde backup encriptado
2. Verificar integridad de datos
3. Reiniciar servicios
4. Validar funcionalidad completa
```

## Compliance y Auditoría

### 1. PCI DSS Requirements
- ✅ Network segmentation (internal networks)
- ✅ Encryption in transit (SSL/TLS)
- ✅ Access controls (user roles)
- ✅ Logging and monitoring
- ✅ Regular updates (container images)

### 2. Logging de Auditoría
```yaml
volumes:
  - audit_logs:/var/log/audit:rw
```

### 3. Retención de Logs
```bash
# Retener logs de transacciones por 7 años (Costa Rica)
find /logs -name "transactions-*.log" -mtime +2555 -delete
```

## Actualizaciones de Seguridad

### 1. Escaneo de Vulnerabilidades
```bash
# Escanear imágenes antes del deploy
docker scan cajacentral/pos-app:latest

# Trivy scan
trivy image cajacentral/pos-app:latest
```

### 2. Actualizaciones Automáticas
```yaml
# Watchtower para actualizaciones
watchtower:
  image: containrrr/watchtower
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock
  command: --schedule "0 0 2 * * *"  # 2 AM daily
```

### 3. Rollback Rápido
```bash
# Mantener 3 versiones anteriores
docker tag pos-app:latest pos-app:backup-$(date +%Y%m%d)
docker-compose up -d  # Nueva versión
# Si hay problemas: docker-compose down && docker tag pos-app:backup-date pos-app:latest
```

## Lista de Verificación de Seguridad

### Pre-Producción
- [ ] Usuarios no-root en todos los contenedores
- [ ] Filesystem de solo lectura habilitado
- [ ] Certificados SSL válidos instalados
- [ ] Secrets management configurado
- [ ] Rate limiting configurado
- [ ] Health checks funcionando
- [ ] Backup automatizado configurado
- [ ] Logging de auditoría habilitado
- [ ] Escaneo de vulnerabilidades completado
- [ ] Plan de recuperación documentado

### Post-Producción
- [ ] Monitoreo de logs activo
- [ ] Alertas de seguridad configuradas
- [ ] Backups verificados semanalmente
- [ ] Certificados monitoreados para expiración
- [ ] Actualizaciones de seguridad programadas
- [ ] Auditorías de acceso mensuales
- [ ] Pruebas de recuperación trimestrales

## Contactos de Emergencia

### Incidentes de Seguridad
- Admin Técnico: +506-XXXX-XXXX
- Email: security@cajacentral.com
- Escalación: Gerencia IT

### Procedimiento de Respuesta
1. Aislar sistema comprometido
2. Preservar evidencia forense
3. Notificar a administración
4. Restaurar desde backup limpio
5. Investigar causa raíz
6. Actualizar procedimientos
