# CLI Commands Reference

The `nimbusfleet` CLI provides command-line access to all platform features.

## Installation

```bash
pip install nimbusfleet-cli
```

Verify installation:

```bash
nimbusfleet --version
```

## Authentication

### Login

Authenticate with your NimbusFleet account:

```bash
nimbusfleet auth login
```

You'll be prompted to enter your API key. Alternatively, set the environment variable:

```bash
export NIMBUSFLEET_API_KEY=nf_live_abc123xyz...
```

### Refresh Token

```bash
nimbusfleet auth refresh
```

!!! note "Session Duration"
    CLI sessions expire after 24 hours. Run `nimbusfleet auth refresh` to extend your session without re-entering credentials.

## Drone Commands

### List Drones

Display all drones in your fleet:

```bash
nimbusfleet drone list
```

Options:
- `--status <status>`: Filter by status (active, idle, offline)
- `--region <region>`: Filter by AWS region
- `--format <format>`: Output format (table, json, yaml)

Example:

```bash
nimbusfleet drone list --status active --format json
```

### Get Drone Details

```bash
nimbusfleet drone get <drone-id>
```

### Create Drone

```bash
nimbusfleet drone create -f drone-config.yaml
```

### Update Drone

```bash
nimbusfleet drone update <drone-id> --enable-failover --telemetry-interval 10s
```

### Delete Drone

```bash
nimbusfleet drone delete <drone-id> --confirm
```

## Flight Commands

### Start Flight

```bash
nimbusfleet flight start <drone-id> --plan <plan-id>
```

Options:
- `--plan <plan-id>`: Flight plan identifier
- `--priority <level>`: Priority level (low, normal, high, emergency)
- `--dry-run`: Validate without executing

### Watch Flight

Stream real-time flight status:

```bash
nimbusfleet flight watch <drone-id>
```

### Return-to-Launch

```bash
nimbusfleet drone rtl <drone-id> --priority emergency
```

### Emergency Land

```bash
nimbusfleet drone emergency-land <drone-id>
```

## Telemetry Commands

### Get Current Telemetry

```bash
nimbusfleet telemetry get <drone-id>
```

### Stream Telemetry

Stream real-time telemetry to terminal:

```bash
nimbusfleet telemetry stream <drone-id> --metrics gps,battery,altitude
```

Options:
- `--metrics <list>`: Comma-separated metric names
- `--format <format>`: Output format (table, json, csv)
- `--output <file>`: Write to file instead of stdout

### Historical Telemetry

Query time-series data:

```bash
nimbusfleet telemetry history <drone-id> --since "2 hours ago" --metrics battery
```

## Integration Commands

### Create Integration

```bash
nimbusfleet integration create -f iot-integration.yaml
```

### List Integrations

```bash
nimbusfleet integration list
```

### Test Integration

```bash
nimbusfleet integration test <integration-name> --drone-id <drone-id>
```

## Diagnostics Commands

### Network Diagnostics

```bash
nimbusfleet diagnostics network <drone-id> --output json
```

### Generate Support Bundle

```bash
nimbusfleet diagnostics bundle <drone-id> --last 24h --output support-bundle.tar.gz
```

## Configuration Commands

### Show Configuration

```bash
nimbusfleet config show
```

### Set Configuration

```bash
nimbusfleet config set default-region us-west-2
nimbusfleet config set output-format json
```

## Command Reference Table

| Command | Description | Example |
|---------|-------------|---------|
| `nimbusfleet auth login` | Authenticate with API key | `nimbusfleet auth login` |
| `nimbusfleet drone list` | List all drones | `nimbusfleet drone list --status active` |
| `nimbusfleet drone get` | Get drone details | `nimbusfleet drone get drone-abc123` |
| `nimbusfleet drone create` | Create new drone | `nimbusfleet drone create -f config.yaml` |
| `nimbusfleet flight start` | Start flight mission | `nimbusfleet flight start drone-abc123 --plan mission-1` |
| `nimbusfleet flight watch` | Watch flight progress | `nimbusfleet flight watch drone-abc123` |
| `nimbusfleet telemetry stream` | Stream real-time data | `nimbusfleet telemetry stream drone-abc123` |
| `nimbusfleet diagnostics network` | Run network diagnostics | `nimbusfleet diagnostics network drone-abc123` |

## CLI Usage Checklist

When using the CLI for production operations:

- [ ] Verify authentication is current (`nimbusfleet auth status`)
- [ ] Test commands in simulation mode first (`--environment simulation`)
- [ ] Enable verbose logging for troubleshooting (`--verbose`)
- [ ] Use `--dry-run` flag for destructive operations
- [ ] Set default region to avoid repeated `--region` flags
- [ ] Configure output format preference (`nimbusfleet config set output-format json`)

## Global Flags

Available on all commands:

- `--verbose, -v`: Enable verbose logging
- `--quiet, -q`: Suppress non-error output
- `--no-color`: Disable colored output
- `--region <region>`: Override default AWS region
- `--profile <profile>`: Use specific configuration profile
- `--output <format>`: Output format (table, json, yaml)

## Example Workflows

### Deploy and Monitor New Drone

```bash
# Create drone from configuration
nimbusfleet drone create -f new-drone.yaml

# Get drone ID from output
DRONE_ID="drone-xyz789"

# Verify drone status
nimbusfleet drone get $DRONE_ID

# Stream telemetry
nimbusfleet telemetry stream $DRONE_ID
```

### Emergency Response

```bash
# Check drone status
nimbusfleet drone get drone-emergency-01

# Initiate return-to-launch
nimbusfleet drone rtl drone-emergency-01 --priority emergency

# Monitor return flight
nimbusfleet flight watch drone-emergency-01
```

## Bash Completion

Enable command auto-completion:

```bash
# For Bash
nimbusfleet completion bash > /etc/bash_completion.d/nimbusfleet

# For Zsh
nimbusfleet completion zsh > /usr/local/share/zsh/site-functions/_nimbusfleet
```

## Related Documentation

- [REST API Reference](../api/rest.md) for HTTP-based integrations
- [Deploy Your First Drone](../../tutorial/deploy-your-first-drone.md) tutorial
- [Troubleshooting Guide](../../tutorial/troubleshoot-field-issues.md) for field operations

---

**CLI Version**: 2.4.0 | **Last Updated**: November 2025
