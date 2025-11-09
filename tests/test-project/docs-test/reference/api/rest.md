# REST API Reference

The NimbusFleet REST API provides programmatic access to fleet management, telemetry, and flight operations.

## Base URL

```
https://api.nimbusfleet.io/v2
```

## Authentication

All API requests require an API key in the `Authorization` header:

```bash
Authorization: Bearer nf_live_abc123xyz...
```

Obtain your API key from the [dashboard](https://app.nimbusfleet.io/settings/api-keys).

!!! warning "Rate Limits"
    - **Standard Plan**: 1,000 requests/hour
    - **Enterprise Plan**: 10,000 requests/hour
    - Rate limit headers included in all responses:
      - `X-RateLimit-Limit`
      - `X-RateLimit-Remaining`
      - `X-RateLimit-Reset`

## Drones

### List Drones

Retrieve all drones in your fleet.

**Endpoint**: `GET /drones`

**Query Parameters**:
- `status` (optional): Filter by status (`active`, `idle`, `maintenance`, `offline`)
- `region` (optional): Filter by AWS region
- `limit` (optional): Number of results (default: 50, max: 200)
- `offset` (optional): Pagination offset

**Example Request**:

```bash
curl -X GET https://api.nimbusfleet.io/v2/drones?status=active&limit=10 \
  -H "Authorization: Bearer nf_live_abc123xyz..."
```

**Example Response** (200 OK):

```json
{
  "drones": [
    {
      "id": "drone-f8a7c2d1",
      "name": "delivery-drone-01",
      "model": "NF-Hawk-X2",
      "status": "active",
      "location": {
        "lat": 37.7749,
        "lon": -122.4194,
        "altitude": 85.3
      },
      "battery": {
        "percent": 78,
        "voltage": 23.4
      },
      "created_at": "2025-10-15T09:24:00Z",
      "last_seen": "2025-11-08T14:35:22Z"
    }
  ],
  "pagination": {
    "total": 47,
    "limit": 10,
    "offset": 0
  }
}
```

### Get Drone Details

Retrieve detailed information for a specific drone.

**Endpoint**: `GET /drones/{drone_id}`

**Example Request**:

```bash
curl -X GET https://api.nimbusfleet.io/v2/drones/drone-f8a7c2d1 \
  -H "Authorization: Bearer nf_live_abc123xyz..."
```

### Create Drone

Register a new drone with your fleet.

**Endpoint**: `POST /drones`

**Request Body**:

```json
{
  "name": "delivery-drone-05",
  "model": "NF-Hawk-X2",
  "region": "us-west-2",
  "environment": "production",
  "capabilities": {
    "max_payload_kg": 5.0,
    "max_range_km": 15.0,
    "max_altitude_m": 120
  },
  "telemetry": {
    "reporting_interval_seconds": 5,
    "metrics": ["gps", "battery", "altitude", "velocity"]
  }
}
```

**Example Response** (201 Created):

```json
{
  "id": "drone-a3f9d2e8",
  "name": "delivery-drone-05",
  "status": "initializing",
  "api_endpoint": "https://api.nimbusfleet.io/v2/drones/drone-a3f9d2e8",
  "telemetry_stream": "wss://telemetry.nimbusfleet.io/stream/drone-a3f9d2e8",
  "created_at": "2025-11-08T14:40:15Z"
}
```

### Update Drone

Modify drone configuration.

**Endpoint**: `PATCH /drones/{drone_id}`

**Request Body**:

```json
{
  "telemetry": {
    "reporting_interval_seconds": 10
  },
  "features": {
    "multi_carrier_failover": true,
    "visual_inertial_odometry": true
  }
}
```

**Example Response** (200 OK):

```json
{
  "id": "drone-f8a7c2d1",
  "updated_at": "2025-11-08T14:42:30Z",
  "changes_applied": 2
}
```

## Flight Operations

### Start Flight

Execute a flight plan.

**Endpoint**: `POST /drones/{drone_id}/flights`

**Request Body**:

```json
{
  "plan_id": "delivery-mission-14",
  "priority": "normal",
  "parameters": {
    "max_speed_mps": 15,
    "cruise_altitude_m": 80
  }
}
```

### Emergency Return-to-Launch

**Endpoint**: `POST /drones/{drone_id}/rtl`

```bash
curl -X POST https://api.nimbusfleet.io/v2/drones/drone-f8a7c2d1/rtl \
  -H "Authorization: Bearer nf_live_abc123xyz..." \
  -d '{"priority": "emergency"}'
```

## Telemetry

### Get Current Telemetry

**Endpoint**: `GET /drones/{drone_id}/telemetry`

**Example Response**:

```json
{
  "drone_id": "drone-f8a7c2d1",
  "timestamp": "2025-11-08T14:45:18Z",
  "gps": {
    "lat": 37.7849,
    "lon": -122.4094,
    "altitude": 82.5,
    "satellites": 12,
    "hdop": 0.8
  },
  "battery": {
    "percent": 65,
    "voltage": 22.8,
    "current_a": 15.2,
    "temperature_c": 38
  },
  "velocity": {
    "ground_speed_mps": 12.3,
    "vertical_speed_mps": 0.2,
    "heading_deg": 245
  },
  "status": "in_flight"
}
```

## Telemetry Dashboard Visualization

![NimbusFleet Telemetry Dashboard](../../assets/dashboard-telemetry.png)

*Real-time telemetry dashboard showing GPS tracking, battery metrics, and flight path visualization.*

## Error Responses

All errors follow this structure:

```json
{
  "error": {
    "code": "DRONE_NOT_FOUND",
    "message": "Drone with ID 'drone-invalid' does not exist",
    "request_id": "req_8f3a2c1d"
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `UNAUTHORIZED` | 401 | Invalid or missing API key |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `DRONE_NOT_FOUND` | 404 | Drone does not exist |
| `INVALID_FLIGHT_PLAN` | 400 | Flight plan validation failed |
| `DRONE_OFFLINE` | 503 | Drone not connected |

## SDK Libraries

- **Python**: `pip install nimbusfleet-sdk`
- **Node.js**: `npm install @nimbusfleet/sdk`
- **Go**: `go get github.com/nimbusfleet/go-sdk`

## Related Resources

- [WebSocket API](websocket.md) for real-time telemetry streaming
- [CLI Commands](../cli/commands.md) for command-line operations
- [Architecture Overview](../../explanation/architecture-overview.md) for system design

---

**API Version**: v2 | **Last Updated**: November 2025
