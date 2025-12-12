# USB Drop Campaign Manager - API Documentation

## Base URL

```
https://api.becomeaninternetghost.com
```

## Authentication

The API supports two authentication methods:

### 1. JWT Token (Web Interface)

```bash
# Login to get tokens
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=admin&password=yourpassword

# Response
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}

# Use in requests
Authorization: Bearer <access_token>
```

### 2. API Key (CLI/Automation)

```bash
# Generate API key via web interface or API
POST /auth/api-keys
Authorization: Bearer <access_token>

{
  "name": "CLI Tool"
}

# Use in requests
X-API-Key: <api_key>
```

## Endpoints

### Campaigns

#### List Campaigns
```http
GET /campaigns
```

Response:
```json
[
  {
    "id": "uuid",
    "name": "Q1 2024 Assessment",
    "client_name": "Acme Corp",
    "status": "active",
    "drive_count": 10,
    "triggered_count": 3,
    "created_at": "2024-01-15T10:00:00Z"
  }
]
```

#### Create Campaign
```http
POST /campaigns

{
  "name": "Q1 2024 Assessment",
  "client_name": "Acme Corp",
  "description": "Quarterly security assessment"
}
```

#### Get Campaign Details
```http
GET /campaigns/{id}
```

#### Update Campaign
```http
PUT /campaigns/{id}

{
  "name": "Updated Name",
  "status": "completed"
}
```

#### Get Campaign Statistics
```http
GET /campaigns/{id}/stats
```

Response:
```json
{
  "total_drives": 10,
  "deployed": 8,
  "triggered": 3,
  "drives_by_status": {
    "created": 1,
    "prepared": 1,
    "deployed": 5,
    "triggered": 3
  }
}
```

---

### Profiles

#### List Profiles
```http
GET /profiles
```

#### Create Profile
```http
POST /profiles

{
  "name": "HR Payroll",
  "description": "HR department payroll documents",
  "scenario_type": "hr",
  "theme": "corporate",
  "token_config": {
    "types": ["dns", "word", "excel"]
  },
  "label_suggestions": ["Payroll Q4", "Benefits 2024"]
}
```

#### Preview Profile
```http
GET /profiles/{id}/preview
```

Response:
```json
{
  "files": [
    {"name": "Payroll_Summary.docx", "type": "word"},
    {"name": "Benefits_Overview.xlsx", "type": "excel"}
  ],
  "tokens": ["dns", "word", "excel"]
}
```

---

### Drives

#### List Drives
```http
GET /drives?campaign_id={uuid}&status={status}
```

#### Create Drive
```http
POST /drives

{
  "campaign_id": "uuid",
  "profile_id": "uuid",
  "label": "HR Payroll Q4"
}
```

Response:
```json
{
  "id": "uuid",
  "unique_code": "USB-A1B2-ACME",
  "status": "created",
  "label": "HR Payroll Q4"
}
```

#### Prepare Drive
Creates tokens and generates files.
```http
POST /drives/{id}/prepare
```

Response:
```json
{
  "id": "uuid",
  "status": "prepared",
  "tokens": [
    {"id": "uuid", "token_type": "dns", "filename": null},
    {"id": "uuid", "token_type": "word", "filename": "Payroll_Summary.docx"}
  ]
}
```

#### Download Drive ZIP
```http
GET /drives/{id}/download
```

Returns a ZIP file containing all drive files.

#### Deploy Drive
Record deployment location.
```http
POST /drives/{id}/deploy

{
  "latitude": 37.7749,
  "longitude": -122.4194,
  "location_description": "Building A lobby",
  "deployed_by": "John Smith"
}
```

#### Get Drive by Code
```http
GET /drives/by-code/{code}
```

#### Get Drive Tokens
```http
GET /drives/{id}/tokens
```

---

### Alerts

#### List Recent Alerts
```http
GET /alerts/recent?hours=24
```

Response:
```json
[
  {
    "id": "uuid",
    "drive_code": "USB-A1B2-ACME",
    "token_type": "word",
    "token_filename": "Payroll_Summary.docx",
    "source_ip": "192.168.1.100",
    "geo_city": "San Francisco",
    "geo_country": "US",
    "triggered_at": "2024-01-15T14:30:00Z"
  }
]
```

#### Get Alert Statistics
```http
GET /alerts/stats?campaign_id={uuid}
```

Response:
```json
{
  "total": 150,
  "today": 5,
  "this_week": 23,
  "unique_ips": 45
}
```

#### Get Map Data
```http
GET /alerts/map?campaign_id={uuid}
```

Response:
```json
{
  "deployments": [
    {
      "drive_code": "USB-A1B2",
      "latitude": 37.7749,
      "longitude": -122.4194,
      "location_description": "Building A",
      "deployed_at": "2024-01-15T10:00:00Z"
    }
  ],
  "triggers": [
    {
      "drive_code": "USB-A1B2",
      "token_type": "word",
      "geo_latitude": 37.7849,
      "geo_longitude": -122.4094,
      "geo_city": "San Francisco",
      "triggered_at": "2024-01-15T14:30:00Z"
    }
  ]
}
```

---

### Content Generation

#### Generate Document
```http
POST /generate/document

{
  "document_type": "memo",
  "topic": "Q4 payroll adjustments",
  "tone": "professional",
  "length": "medium"
}
```

Response:
```json
{
  "content": "MEMORANDUM\n\nTo: All Employees\nFrom: HR Department...",
  "filename": "memo_payroll_adjustments.docx"
}
```

#### Generate Image
```http
POST /generate/image

{
  "prompt": "Professional corporate office building",
  "style": "photorealistic",
  "size": "1024x1024"
}
```

---

### Reports

#### Get Campaign Report
```http
GET /reports/campaign/{id}
```

Response:
```json
{
  "total_drives": 10,
  "deployed": 8,
  "triggered": 3,
  "total_triggers": 15,
  "status_distribution": {
    "created": 1,
    "prepared": 1,
    "deployed": 5,
    "triggered": 3
  },
  "triggers_by_day": {
    "2024-01-15": 5,
    "2024-01-16": 10
  },
  "triggers_by_type": {
    "dns": 3,
    "word": 8,
    "excel": 4
  },
  "top_drives": [
    {
      "id": "uuid",
      "unique_code": "USB-A1B2",
      "trigger_count": 5,
      "first_trigger": "2024-01-15T14:30:00Z"
    }
  ]
}
```

#### Export Campaign CSV
```http
GET /reports/export/{id}/csv
```

Returns a CSV file with all campaign data.

---

### Webhooks

#### CanaryTokens Webhook
Receives trigger notifications from CanaryTokens.
```http
POST /webhooks/canary

{
  "token": "canary-token-id",
  "src_ip": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "additional_data": {}
}
```

---

## Error Responses

All errors follow this format:
```json
{
  "detail": "Error message here"
}
```

Common HTTP status codes:
- `400` - Bad Request (invalid input)
- `401` - Unauthorized (missing/invalid auth)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

## Rate Limiting

API requests are limited to:
- 100 requests per minute for authenticated users
- 10 requests per minute for unauthenticated endpoints

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1705329600
```
