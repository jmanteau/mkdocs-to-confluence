# Troubleshoot Field Issues

When operating drones in real-world conditions, you may encounter connectivity, navigation, or hardware issues. This guide helps you diagnose and resolve common field problems.

!!! warning "Safety First"
    Always follow local aviation regulations. If a drone exhibits erratic behavior, use the emergency land feature immediately: `nimbusfleet drone emergency-land <drone-id>`

## Common Field Issues

### Issue 1: Intermittent Connectivity Loss

#### Symptoms
- Telemetry data drops every 30-60 seconds
- Dashboard shows "DISCONNECTED" status intermittently
- Flight commands delayed or ignored

#### Diagnostic Steps

Run a connectivity diagnostic:

```bash
nimbusfleet diagnostics network <drone-id> --output json
```

Sample output:

```json
{
  "drone_id": "drone-f8a7c2d1",
  "timestamp": "2025-11-08T14:32:18Z",
  "network": {
    "signal_strength": -87,
    "packet_loss": 12.4,
    "latency_ms": 245,
    "carrier": "LTE",
    "last_disconnect": "2025-11-08T14:30:12Z"
  },
  "status": "DEGRADED",
  "recommendation": "Poor signal strength. Consider RTL or find alternate route."
}
```

#### Resolution

**For signal strength < -85 dBm**:

1. ~~Use the `set-fallback-network` command~~ (deprecated in v2.3)
2. <ins>Enable multi-carrier failover</ins>: `nimbusfleet drone update <drone-id> --enable-failover`
3. Reduce reporting interval to conserve bandwidth: `--telemetry-interval 15s`

### Issue 2: GPS Drift in Urban Environments

#### Symptoms
- Drone position jumps 5-10 meters unexpectedly
- Waypoint accuracy degraded
- "GPS_WEAK" warning in logs

#### Field Checklist

Before flight, verify:

- [ ] GPS lock achieved (minimum 8 satellites)
- [ ] HDOP < 2.0 (horizontal dilution of precision)
- [ ] No nearby RF interference sources
- [ ] Magnetometer calibrated within last 7 days
- [ ] ~~Use GPS-only mode~~ (deprecated)
- [ ] <ins>Enable GPS+GLONASS fusion mode</ins>

#### Resolution Steps

##### Step 1: Check Satellite Count

```bash
nimbusfleet telemetry get <drone-id> --metric gps
```

##### Step 2: Recalibrate Sensors

```bash
nimbusfleet drone calibrate <drone-id> --sensors magnetometer,gps
```

##### Step 3: Enable Assisted Positioning

<ins>New in v2.4</ins>: Visual-inertial odometry for urban flights

```bash
nimbusfleet drone update <drone-id> --enable-vio
```

### Issue 3: Battery Degradation Faster Than Expected

#### Symptoms
- Battery depletes 20%+ faster than flight plan estimate
- Voltage drops sharply under load
- Unexpected low-battery RTL triggers

#### Diagnostic JSON Output

```json
{
  "drone_id": "drone-f8a7c2d1",
  "battery": {
    "current_voltage": 22.1,
    "design_voltage": 24.0,
    "capacity_mah": 5200,
    "health_percent": 68,
    "charge_cycles": 247,
    "temperature_c": 42,
    "cells": [
      {"cell": 1, "voltage": 3.68, "status": "OK"},
      {"cell": 2, "voltage": 3.65, "status": "OK"},
      {"cell": 3, "voltage": 3.62, "status": "OK"},
      {"cell": 4, "voltage": 3.71, "status": "OK"},
      {"cell": 5, "voltage": 3.59, "status": "WEAK"},
      {"cell": 6, "voltage": 3.66, "status": "OK"}
    ]
  },
  "recommendation": "Cell 5 voltage low. Consider battery replacement."
}
```

#### Resolution

1. **Cell Balancing**: Perform full charge cycle with balancing enabled
2. **Temperature Management**: Avoid flights when battery temp > 40°C
3. **Replacement Criteria**: Replace battery when health < 70%

!!! note "Battery Health Monitoring"
    Enable automatic health tracking: `nimbusfleet drone update <drone-id> --battery-monitoring advanced`

## Emergency Procedures

### Return-to-Launch (RTL)

Immediately return drone to launch point:

```bash
nimbusfleet drone rtl <drone-id> --priority emergency
```

### Emergency Land

Force immediate landing at current location:

```bash
nimbusfleet drone emergency-land <drone-id>
```

!!! warning "Use Only in Critical Situations"
    Emergency land does not check terrain safety. Use RTL when possible.

## Field Operations Checklist

Before each deployment:

- [ ] Pre-flight inspection completed
- [ ] Battery health > 75%
- [ ] GPS lock with 10+ satellites
- [ ] Connectivity test passed (signal > -80 dBm)
- [ ] Weather conditions within operational limits
- [ ] Airspace clearance obtained
- [ ] Emergency procedures reviewed with ground crew
- [ ] Backup landing zones identified

## Accessing Support Logs

Generate a support bundle for technical assistance:

```bash
nimbusfleet diagnostics bundle <drone-id> --last 24h --output support-bundle.tar.gz
```

Submit to support: support@nimbusfleet.io

## Next Steps

- Review [REST API](../reference/api/rest.md) for custom alerting
- Read [Architecture Overview](../explanation/architecture-overview.md) to understand system resilience
- Check [WebSocket API](../reference/api/websocket.md) for real-time monitoring integration

---

**Last Updated**: November 2025 | **Applies to**: NimbusFleet v2.3+
