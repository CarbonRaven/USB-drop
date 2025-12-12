# USB Drop CLI - User Guide

## Installation

```bash
# From source
cd usb-drop-cli
pip install -e .

# Or with pip
pip install usb-drop-cli
```

## Configuration

Before using the CLI, configure your API connection:

```bash
# Set the API server URL
usb-drop config set-api https://api.becomeaninternetghost.com

# Set your API key (generate from web interface)
usb-drop config set-key your-api-key-here

# Optionally set a default campaign
usb-drop config set-campaign campaign-uuid

# Verify configuration
usb-drop config show
```

Configuration is stored in `~/.usb-drop/config.yaml`.

## Commands

### Campaigns

```bash
# List all campaigns
usb-drop list-campaigns
```

### Profiles

```bash
# List available USB profiles
usb-drop list-profiles
```

### Drives

```bash
# List all drives
usb-drop list-drives

# Filter by campaign
usb-drop list-drives --campaign <campaign-id>

# Filter by status
usb-drop list-drives --status deployed
```

### Preparing a Drive

```bash
# Interactive mode (recommended for first-time use)
usb-drop prepare --interactive

# Direct mode
usb-drop prepare --campaign <campaign-id> --profile <profile-id> --label "HR Payroll Q4"

# Using default campaign
usb-drop prepare --profile <profile-id> --label "IT Support"
```

The prepare command:
1. Creates a new drive record
2. Generates tokens with CanaryTokens
3. Returns the unique drive code

### Downloading Drive Files

```bash
# Download as ZIP file
usb-drop download <drive-id>

# Save to specific location
usb-drop download <drive-id> --output /path/to/file.zip

# Write directly to USB drive
usb-drop download <drive-id> --usb

# Clear USB before writing
usb-drop download <drive-id> --usb --clear
```

### Deploying a Drive

Record the physical deployment location:

```bash
# With coordinates
usb-drop deploy <drive-id> --lat 37.7749 --lon -122.4194 --location "Building A lobby" --by "John Smith"

# Interactive mode
usb-drop deploy <drive-id> --interactive
```

### Checking Drive Status

```bash
# Get status by drive code
usb-drop status USB-A1B2-ACME
```

### Viewing Alerts

```bash
# Recent alerts (last 24 hours)
usb-drop alerts

# Last 7 days
usb-drop alerts --hours 168
```

## Workflow Example

### Complete USB Preparation Workflow

```bash
# 1. List available campaigns
usb-drop list-campaigns

# 2. List available profiles
usb-drop list-profiles

# 3. Prepare a new drive (interactive)
usb-drop prepare --interactive
# Select campaign: "Q1 2024 Assessment"
# Select profile: "HR Payroll"
# Enter label: "Payroll Q4 2024"
# Output: Drive created: USB-A1B2-ACME

# 4. Download to USB drive
usb-drop download <drive-id> --usb --clear
# Select USB drive: /Volumes/UNTITLED
# Files written successfully

# 5. Record deployment
usb-drop deploy <drive-id> --interactive
# Enter latitude: 37.7749
# Enter longitude: -122.4194
# Enter location: Building A lobby, near elevator
# Enter deployed by: John Smith
# Deployment recorded!

# 6. Monitor for triggers
usb-drop alerts --hours 1
```

### Batch Operations

For preparing multiple drives:

```bash
#!/bin/bash

CAMPAIGN="your-campaign-id"
PROFILE="your-profile-id"

for i in {1..10}; do
    usb-drop prepare \
        --campaign $CAMPAIGN \
        --profile $PROFILE \
        --label "Drive $i"
done
```

## Environment Variables

You can also configure the CLI using environment variables:

```bash
export USB_DROP_API_URL=https://api.becomeaninternetghost.com
export USB_DROP_API_KEY=your-api-key
```

## Troubleshooting

### Connection Errors

```bash
# Check configuration
usb-drop config show

# Test API connectivity
curl -H "X-API-Key: your-key" https://api.becomeaninternetghost.com/auth/me
```

### USB Drive Not Detected

The CLI looks for USB drives in:
- macOS: `/Volumes/`
- Linux: `/media/` and `/mnt/`
- Windows: Drive letters other than C:

Ensure your USB drive is properly mounted and accessible.

### Permission Errors

```bash
# macOS/Linux: Run with sudo if needed
sudo usb-drop download <drive-id> --usb
```

## Output Formats

The CLI uses Rich for formatted output. Tables and status information are displayed with colors and formatting for easy reading.

For machine-readable output, use the API directly or parse the JSON responses.
