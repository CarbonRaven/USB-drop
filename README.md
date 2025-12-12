# USB Drop Campaign Management System

A comprehensive platform for managing USB drop penetration testing campaigns with integrated CanaryTokens, real-time alerting, and AI-generated content.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Vue.js](https://img.shields.io/badge/Vue.js-3.x-green.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-teal.svg)
![Docker](https://img.shields.io/badge/Docker-Compose-blue.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## Overview

This system streamlines USB drop security assessments by providing:

- **Automated Token Generation** - Integration with self-hosted CanaryTokens for DNS, Word, Excel, PDF, and other token types
- **Campaign Management** - Organize drives by client, track deployment locations, and monitor trigger events
- **USB Profiles** - Reusable templates with AI-generated content (documents, images) for realistic scenarios
- **Real-time Alerts** - WebSocket-based notifications with Slack integration
- **Geographic Tracking** - Map visualization of drop locations and trigger sources
- **CLI Tool** - Command-line interface for field operators preparing and deploying drives

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

All services run in Docker containers on a single VPS with Caddy providing automatic HTTPS.

## Features

### Campaign Manager Web UI
- Dashboard with real-time statistics
- Campaign and profile management
- Drive preparation wizard
- Interactive map with deployment/trigger markers
- Alert feed with filtering
- Campaign reports with charts and CSV export

### CLI Tool
- Interactive and scripted modes
- Direct USB drive writing
- Batch drive preparation
- Field deployment recording with GPS

### Landing Pages
- Multiple themed redirect pages (corporate, login, maintenance, etc.)
- Visitor logging before redirect
- Configurable target URLs

## Technology Stack

| Component | Technology |
|-----------|------------|
| Backend API | FastAPI (Python 3.11+) |
| Frontend | Vue 3 + Vite + Tailwind CSS |
| Database | PostgreSQL 16 |
| Container Orchestration | Docker Compose |
| CanaryTokens | Self-hosted Docker deployment |
| Reverse Proxy | Caddy (automatic HTTPS) |
| AI Generation | OpenAI API (GPT-4 + DALL-E 3) |
| Maps | Leaflet.js + OpenStreetMap |
| Real-time | WebSockets |

## Quick Start

### Prerequisites

- VPS with 8GB+ RAM (Debian 13 recommended)
- Docker and Docker Compose
- Two domains pointed to your VPS

### 1. Clone and Configure

```bash
git clone https://github.com/CarbonRaven/USB-drop.git
cd USB-drop

# Copy and edit environment configuration
cp .env.example .env
nano .env
```

### 2. Configure Required Variables

```bash
# Required settings
VPS_IP=your.server.ip
DB_PASSWORD=secure-database-password
JWT_SECRET_KEY=secure-random-string
ADMIN_PASSWORD=secure-admin-password

# CanaryTokens
CANARY_DOMAIN=your-canary-domain.com
FACTORY_AUTH=random-auth-token

# Optional: AI content generation
OPENAI_API_KEY=sk-your-openai-key
```

### 3. Deploy

```bash
# Start CanaryTokens stack
docker compose -f docker-compose.canarytokens.yml up -d

# Start Campaign Manager
docker compose up -d --build
```

### 4. Access

- **Campaign Manager**: `https://app.yourdomain.com`
- **API**: `https://api.yourdomain.com`
- **CanaryTokens**: `https://tokens.your-canary-domain.com`

## CLI Installation

```bash
cd usb-drop-cli
pip install -e .

# Configure
usb-drop config set-api https://api.yourdomain.com
usb-drop config set-key your-api-key

# Prepare a drive
usb-drop prepare --interactive
```

## Project Structure

```
USB-drop/
├── campaign-api/          # FastAPI backend
│   ├── app/
│   │   ├── models/        # SQLAlchemy models
│   │   ├── routers/       # API endpoints
│   │   └── services/      # Business logic
│   └── Dockerfile
├── campaign-frontend/     # Vue 3 frontend
│   ├── src/
│   │   ├── views/         # Page components
│   │   ├── stores/        # Pinia state
│   │   └── services/      # API client
│   └── Dockerfile
├── usb-drop-cli/          # Python CLI tool
│   └── usb_drop/
├── landing-pages/         # Redirect pages
│   └── rickroll/
├── docs/                  # Documentation
│   ├── DEPLOYMENT.md
│   ├── API.md
│   └── CLI.md
├── docker-compose.yml
├── docker-compose.canarytokens.yml
└── Caddyfile
```

## Documentation

- [Deployment Guide](docs/DEPLOYMENT.md) - Full VPS setup instructions
- [API Reference](docs/API.md) - Complete endpoint documentation
- [CLI Guide](docs/CLI.md) - Command-line tool usage

## Workflow Example

1. **Create Campaign** - Set up a new assessment for a client
2. **Create Profile** - Define USB contents (file types, tokens, AI prompts)
3. **Prepare Drives** - Generate tokens and create drive packages
4. **Deploy** - Write files to USB drives, record drop locations
5. **Monitor** - Watch for token triggers in real-time
6. **Report** - Generate campaign summary with maps and statistics

## Security Considerations

- All traffic encrypted via automatic HTTPS (Caddy + Let's Encrypt)
- JWT authentication with short-lived tokens
- API keys for CLI/automation access
- Database isolated in Docker network
- Webhook signature validation

## License

MIT License - See [LICENSE](LICENSE) for details.

## Disclaimer

This tool is designed for authorized security assessments only. Always obtain proper authorization before conducting USB drop tests. Misuse of this software may violate laws and regulations.
