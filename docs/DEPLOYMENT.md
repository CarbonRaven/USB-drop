# USB Drop Campaign Manager - Deployment Guide

## Prerequisites

- VPS with at least 8GB RAM (Debian 13 recommended)
- Docker and Docker Compose installed
- Two domains pointed to your VPS IP:
  - `subproject55.com` - for CanaryTokens
  - `becomeaninternetghost.com` - for Campaign Manager

## Quick Start

### 1. Clone and Configure

```bash
# Clone the repository
git clone <repository-url> usb-drop-system
cd usb-drop-system

# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

### 2. Configure Environment Variables

Edit `.env` with your settings:

```bash
# Required settings
VPS_IP=your.server.ip
DB_PASSWORD=secure-database-password
JWT_SECRET=secure-random-string-for-jwt
ADMIN_USERNAME=admin
ADMIN_PASSWORD=secure-admin-password

# CanaryTokens
CANARY_DOMAIN=subproject55.com
FACTORY_AUTH=random-auth-token-for-canary-api

# Optional: OpenAI for AI content generation
OPENAI_API_KEY=sk-your-openai-key

# Optional: Slack notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
```

### 3. Deploy CanaryTokens

```bash
# Start CanaryTokens stack
docker compose -f docker-compose.canarytokens.yml up -d

# Verify it's running
docker compose -f docker-compose.canarytokens.yml ps
```

### 4. Deploy Campaign Manager

```bash
# Build and start all services
docker compose up -d --build

# Check status
docker compose ps

# View logs
docker compose logs -f
```

### 5. Initialize Database

The database will be automatically initialized on first run. An admin user will be created with the credentials from your `.env` file.

### 6. Access the Application

- Campaign Manager: `https://app.becomeaninternetghost.com`
- API: `https://api.becomeaninternetghost.com`
- CanaryTokens: `https://tokens.subproject55.com`
- RickRoll Landing: `https://rick.becomeaninternetghost.com`

## DNS Configuration

Add the following DNS records for each domain:

### subproject55.com
```
A     @           -> VPS_IP
A     tokens      -> VPS_IP
```

### becomeaninternetghost.com
```
A     @           -> VPS_IP
A     app         -> VPS_IP
A     api         -> VPS_IP
A     rick        -> VPS_IP
A     *           -> VPS_IP  (wildcard for custom landing pages)
```

## SSL/TLS

Caddy automatically obtains and renews Let's Encrypt certificates. No manual configuration needed.

## Updating

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker compose up -d --build

# Run migrations if needed
docker compose exec api alembic upgrade head
```

## Backup

### Database Backup
```bash
# Create backup
docker compose exec postgres pg_dump -U usbdrop usbdrop > backup.sql

# Restore backup
cat backup.sql | docker compose exec -T postgres psql -U usbdrop usbdrop
```

### Volume Backup
```bash
# Backup all volumes
docker run --rm -v usb-drop-system_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres-backup.tar.gz /data
```

## Troubleshooting

### Check Service Logs
```bash
docker compose logs api
docker compose logs frontend
docker compose logs caddy
```

### Restart Services
```bash
docker compose restart api
docker compose restart frontend
```

### Reset Database
```bash
docker compose down
docker volume rm usb-drop-system_postgres_data
docker compose up -d
```

### Check Caddy Certificates
```bash
docker compose exec caddy caddy list-certificates
```

## Security Considerations

1. **Change Default Credentials**: Always change the default admin password
2. **Firewall**: Only expose ports 80 and 443
3. **Updates**: Regularly update Docker images
4. **Backups**: Schedule regular database backups
5. **Monitoring**: Set up log monitoring for security events

## Resource Monitoring

```bash
# Check resource usage
docker stats

# Check disk space
df -h
```

## Architecture

```
                    Internet
                        |
                    [Caddy]
                   /   |   \
                  /    |    \
        [Frontend] [API] [CanaryTokens]
                   |
              [PostgreSQL]
```

All services communicate through an internal Docker network. Only Caddy is exposed to the internet.
