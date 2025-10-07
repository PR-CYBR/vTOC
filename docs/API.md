# API Documentation

## Base URL

```
http://localhost/api
```

## Authentication

Currently, the API does not require authentication. In production, implement JWT or OAuth2.

## Response Format

All responses are in JSON format.

### Success Response

```json
{
  "id": 1,
  "name": "Example",
  "status": "active"
}
```

### Error Response

```json
{
  "detail": "Error message here"
}
```

## Operations API

### List Operations

**Endpoint:** `GET /api/operations/`

**Response:**
```json
[
  {
    "id": 1,
    "name": "Operation Alpha",
    "code_name": "ALPHA-001",
    "description": "Strategic operation",
    "status": "planning",
    "priority": "high",
    "created_at": "2024-01-01T00:00:00"
  }
]
```

### Get Operation

**Endpoint:** `GET /api/operations/{id}`

**Parameters:**
- `id` (path): Operation ID

**Response:** Single operation object

### Create Operation

**Endpoint:** `POST /api/operations/`

**Request Body:**
```json
{
  "name": "Operation Bravo",
  "code_name": "BRAVO-001",
  "description": "Tactical operation",
  "status": "planning",
  "priority": "medium"
}
```

**Response:** Created operation object

### Update Operation

**Endpoint:** `PUT /api/operations/{id}`

**Parameters:**
- `id` (path): Operation ID

**Request Body:** Same as create

**Response:** Updated operation object

### Delete Operation

**Endpoint:** `DELETE /api/operations/{id}`

**Parameters:**
- `id` (path): Operation ID

**Response:**
```json
{
  "message": "Operation deleted successfully"
}
```

## Missions API

### List Missions

**Endpoint:** `GET /api/missions/`

**Query Parameters:**
- `operation_id` (optional): Filter by operation

**Response:**
```json
[
  {
    "id": 1,
    "operation_id": 1,
    "name": "Mission One",
    "description": "First mission",
    "status": "pending",
    "priority": "high",
    "assigned_to": "Team Alpha",
    "created_at": "2024-01-01T00:00:00"
  }
]
```

### Get Mission

**Endpoint:** `GET /api/missions/{id}`

**Parameters:**
- `id` (path): Mission ID

**Response:** Single mission object

### Create Mission

**Endpoint:** `POST /api/missions/`

**Request Body:**
```json
{
  "operation_id": 1,
  "name": "Mission Two",
  "description": "Second mission",
  "status": "pending",
  "priority": "medium",
  "assigned_to": "Team Bravo"
}
```

**Response:** Created mission object

### Update Mission

**Endpoint:** `PUT /api/missions/{id}`

**Parameters:**
- `id` (path): Mission ID

**Request Body:** Same as create

**Response:** Updated mission object

### Delete Mission

**Endpoint:** `DELETE /api/missions/{id}`

**Parameters:**
- `id` (path): Mission ID

**Response:**
```json
{
  "message": "Mission deleted successfully"
}
```

## Assets API

### List Assets

**Endpoint:** `GET /api/assets/`

**Query Parameters:**
- `asset_type` (optional): Filter by type

**Response:**
```json
[
  {
    "id": 1,
    "name": "Drone Alpha",
    "asset_type": "drone",
    "status": "available",
    "location": "Base Camp",
    "specifications": {
      "model": "DJI-X1",
      "range": "10km"
    },
    "assigned_to": null,
    "created_at": "2024-01-01T00:00:00"
  }
]
```

### Get Asset

**Endpoint:** `GET /api/assets/{id}`

**Parameters:**
- `id` (path): Asset ID

**Response:** Single asset object

### Create Asset

**Endpoint:** `POST /api/assets/`

**Request Body:**
```json
{
  "name": "Vehicle Bravo",
  "asset_type": "vehicle",
  "status": "available",
  "location": "Warehouse",
  "specifications": {
    "type": "4x4",
    "capacity": "6 persons"
  },
  "assigned_to": null
}
```

**Response:** Created asset object

### Update Asset

**Endpoint:** `PUT /api/assets/{id}`

**Parameters:**
- `id` (path): Asset ID

**Request Body:** Same as create

**Response:** Updated asset object

### Delete Asset

**Endpoint:** `DELETE /api/assets/{id}`

**Parameters:**
- `id` (path): Asset ID

**Response:**
```json
{
  "message": "Asset deleted successfully"
}
```

## Intelligence API

### List Intelligence Reports

**Endpoint:** `GET /api/intel/`

**Query Parameters:**
- `mission_id` (optional): Filter by mission

**Response:**
```json
[
  {
    "id": 1,
    "mission_id": 1,
    "title": "Reconnaissance Report",
    "content": "Detailed findings...",
    "classification": "confidential",
    "source": "Field Agent",
    "reliability": "verified",
    "reported_by": "Agent Smith",
    "report_date": "2024-01-01T00:00:00"
  }
]
```

### Get Intelligence Report

**Endpoint:** `GET /api/intel/{id}`

**Parameters:**
- `id` (path): Report ID

**Response:** Single report object

### Create Intelligence Report

**Endpoint:** `POST /api/intel/`

**Request Body:**
```json
{
  "mission_id": 1,
  "title": "Surveillance Report",
  "content": "Observed activities...",
  "classification": "secret",
  "source": "Drone",
  "reliability": "probable",
  "reported_by": "Analyst Jones"
}
```

**Response:** Created report object

### Delete Intelligence Report

**Endpoint:** `DELETE /api/intel/{id}`

**Parameters:**
- `id` (path): Report ID

**Response:**
```json
{
  "message": "Intelligence report deleted successfully"
}
```

## Agents API

### List Agents

**Endpoint:** `GET /api/agents/`

**Response:**
```json
[
  {
    "id": 1,
    "name": "Monitor Agent",
    "agent_type": "monitor",
    "status": "idle",
    "description": "System monitoring agent",
    "configuration": {
      "interval": 300
    },
    "last_run": null,
    "created_at": "2024-01-01T00:00:00"
  }
]
```

### Get Agent

**Endpoint:** `GET /api/agents/{id}`

**Parameters:**
- `id` (path): Agent ID

**Response:** Single agent object

### Create Agent

**Endpoint:** `POST /api/agents/`

**Request Body:**
```json
{
  "name": "Custom Agent",
  "agent_type": "executor",
  "description": "Custom automation agent",
  "configuration": {
    "schedule": "*/15 * * * *"
  }
}
```

**Response:** Created agent object

### Start Agent

**Endpoint:** `POST /api/agents/{id}/start`

**Parameters:**
- `id` (path): Agent ID

**Response:**
```json
{
  "message": "Agent Custom Agent started",
  "status": "running"
}
```

### Stop Agent

**Endpoint:** `POST /api/agents/{id}/stop`

**Parameters:**
- `id` (path): Agent ID

**Response:**
```json
{
  "message": "Agent Custom Agent stopped",
  "status": "stopped"
}
```

### Delete Agent

**Endpoint:** `DELETE /api/agents/{id}`

**Parameters:**
- `id` (path): Agent ID

**Response:**
```json
{
  "message": "Agent deleted successfully"
}
```

## Health & Metrics

### Health Check

**Endpoint:** `GET /api/health`

**Response:**
```json
{
  "status": "healthy",
  "service": "vTOC Backend API"
}
```

### Metrics

**Endpoint:** `GET /api/metrics`

**Response:**
```json
{
  "service": "vtoc-backend",
  "endpoints": [
    "/api/operations",
    "/api/missions",
    "/api/assets",
    "/api/intel",
    "/api/agents"
  ]
}
```

## Status Codes

- `200 OK`: Success
- `201 Created`: Resource created
- `204 No Content`: Success with no content
- `400 Bad Request`: Invalid request
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

## Data Types

### Operation Status
- `planning`
- `active`
- `completed`
- `cancelled`

### Mission Status
- `pending`
- `in_progress`
- `completed`
- `failed`

### Priority Levels
- `low`
- `medium`
- `high`
- `critical`

### Asset Status
- `available`
- `deployed`
- `maintenance`
- `retired`

### Intelligence Classification
- `unclassified`
- `confidential`
- `secret`

### Intelligence Reliability
- `verified`
- `probable`
- `possible`
- `doubtful`

### Agent Status
- `idle`
- `running`
- `error`
- `stopped`

### Agent Types
- `monitor`
- `analyzer`
- `executor`
- `coordinator`
