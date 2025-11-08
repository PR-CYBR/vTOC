# PR-CYBR RF Engine

FISSURE-class RF capabilities for vTOC (clean-room implementation, MIT licensed).

⚠️ **License Notice**: This is a clean-room implementation designed for feature parity with FISSURE. No GPL code was copied. Design is guided by public FISSURE documentation only.

## Features

- 📡 **Multi-Vendor SDR Support**: RTL-SDR, HackRF, USRP, LimeSDR via SoapySDR abstraction
- 📊 **IQ Capture**: SigMF-compliant recording with metadata
- 🔍 **Signal Classification**: ML-based (ONNX) + DSP heuristics
- 🔌 **Protocol Decoding**: Pluggable architecture (OOK, FSK, IEEE 802.15.4, LoRa stubs)
- 📡 **Transmit/Replay**: Gated TX with multi-layer security controls (disabled by default)
- 🗄️ **Archive**: PostgreSQL + S3/MinIO for signal storage and search
- 📈 **Live Streaming**: WebSocket PSD/IQ/constellation visualization
- 🤖 **Agent Integration**: vTOC AgentKit tasks for automated RF workflows
- 🔒 **Security**: RBAC, audit logging, TX whitelist enforcement

## Quick Start (RX-only)

### Prerequisites

- Python 3.11+
- Poetry or pip
- GNU Radio 3.10
- SoapySDR + device drivers
- PostgreSQL
- Optional: MinIO for S3-compatible storage

### Installation

```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y gnuradio soapysdr-tools \
    libsoapysdr-dev rtl-sdr librtlsdr-dev \
    libuhd-dev uhd-host hackrf libhackrf-dev \
    liblimesuite-dev limesuite

# Install Python dependencies
cd services/rf-engine
poetry install
# or
pip install -r requirements.txt
```

### Configuration

```bash
# Copy and edit environment file
cp .env.example.rf .env
nano .env

# Minimal RX-only setup:
# PRCYBR_STATION_ID=vtoc-001
# RF_TX_ENABLED=false  (default, KEEP THIS)
# RF_DEVICES_ALLOWLIST=rtlsdr  (or your device type)
```

### Running

```bash
# Start the RF Engine server
poetry run rf-engine
# or
python -m rfengine.main

# Server runs on http://localhost:8000
# Health check: curl http://localhost:8000/healthz
# Metrics: curl http://localhost:8000/metrics
```

### Testing Device Detection

```bash
# List detected SDR devices
SoapySDRUtil --find

# Expected output:
# Found device 0
#   driver = rtlsdr
#   label = Generic RTL2832U OEM :: 00000001
#   ...
```

## Docker Deployment

### Build Image

```bash
docker build -t prcybr-rf-engine:latest .
```

### Run Container

```bash
docker run -d \
  --name rf-engine \
  --device /dev/bus/usb:/dev/bus/usb \
  -e PRCYBR_STATION_ID=vtoc-001 \
  -e RF_TX_ENABLED=false \
  -p 8000:8000 \
  -v rf_sigmf:/data/sigmf \
  prcybr-rf-engine:latest
```

### Docker Compose Integration

See main `docker-compose.yml` in repository root. The RF Engine service is included with proper device passthrough and volume mounts.

## API Overview

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/healthz` | GET | Health check |
| `/metrics` | GET | Prometheus metrics |
| `/api/v2/rf/info` | GET | RF engine status |

### Device Management (Planned)

```
GET  /api/v2/rf/devices/list
POST /api/v2/rf/devices/{id}/test
```

### Capture Control (Planned)

```
POST /api/v2/rf/capture/start
POST /api/v2/rf/capture/stop
GET  /api/v2/rf/capture/status
```

### Classification (Planned)

```
POST /api/v2/rf/classify/run
```

### Protocol Decoding (Planned)

```
POST /api/v2/rf/protocol/decode
POST /api/v2/rf/protocol/craft  (requires RF_ADMIN + TX enabled)
```

### Replay/Transmit (Planned, Gated)

```
POST /api/v2/rf/replay/start  (requires RF_ADMIN + TX enabled + whitelist)
POST /api/v2/rf/replay/stop
```

### Archive (Planned)

```
GET  /api/v2/rf/archive/search
POST /api/v2/rf/archive/playlist
```

### WebSocket Streaming (Planned)

```
WS /api/v2/rf/stream/psd
WS /api/v2/rf/stream/iq
```

## SigMF Metadata

All captures include SigMF-compliant metadata:

**Required Fields**:
- `core:datatype` (e.g., `cf32_le`)
- `core:sample_rate`
- `core:frequency`
- `core:hw`

**PR-CYBR Extensions**:
- `prcybr:station_id`
- `prcybr:division`
- `prcybr:lat` / `prcybr:lon` (if GPS available)

Example:
```json
{
  "global": {
    "core:datatype": "cf32_le",
    "core:sample_rate": 2000000,
    "core:frequency": 915000000,
    "core:hw": "RTL-SDR Generic",
    "core:version": "1.0.0",
    "prcybr:station_id": "vtoc-001",
    "prcybr:division": "DIV-PR-001"
  },
  "captures": [
    {
      "core:sample_start": 0,
      "core:frequency": 915000000
    }
  ],
  "annotations": []
}
```

## Security & Compliance

### TX Gating (Default: Disabled)

Transmit capabilities are **disabled by default** for safety and regulatory compliance.

To enable TX (⚠️ **READ SECURITY DOCS FIRST**):

1. Set `RF_TX_ENABLED=true`
2. Populate `RF_TX_WHITELIST_FREQS_MHZ` with allowed frequencies
3. Ensure user has `RF_ADMIN` role
4. Obtain valid `tx_guard_token` from backend

All TX operations are fully audited with operator identity.

### RBAC Roles

- **RF_ADMIN**: Full TX + replay access
- **RF_ANALYST**: RX + analysis only
- **OPS/INTEL**: View-only access

### Regulatory Notes

- **RX-only mode** (default) is generally legal in most jurisdictions
- **TX requires license** in most countries (amateur radio, ISM bands, etc.)
- Consult `docs/RF/LEGAL.md` and local regulations before enabling TX
- Example recipes focus on RX-only use cases

## Development

### Project Structure

```
services/rf-engine/
├── rfengine/
│   ├── main.py           # FastAPI app
│   ├── config.py         # Pydantic settings
│   ├── devices/          # SoapySDR abstraction
│   ├── capture/          # RX graphs, SigMF writer
│   ├── replay/           # TX graphs (gated)
│   ├── classify/         # ML + DSP classification
│   ├── protocols/        # Plugin architecture
│   ├── archive/          # Database + S3 adapter
│   ├── security/         # TX gating, RBAC, audit
│   ├── telemetry/        # vTOC telemetry events
│   └── ws/               # WebSocket streaming
├── tests/
│   ├── fixtures/         # IQ test files
│   └── ...
├── pyproject.toml
├── Dockerfile
└── README.md
```

### Running Tests

```bash
poetry run pytest
# or
pytest -v --cov=rfengine
```

### Code Quality

```bash
# Linting
poetry run ruff check rfengine

# Type checking
poetry run mypy rfengine

# Formatting
poetry run black rfengine
```

## Roadmap

See `docs/RF/RF-ROADMAP.md` for detailed implementation plan.

**Current Status**: Phase 1 - Service Skeleton ✅

- [x] Project structure
- [x] Configuration (Pydantic Settings)
- [x] FastAPI skeleton
- [x] Health/metrics endpoints
- [x] Docker support
- [ ] Device management
- [ ] Capture pipeline
- [ ] Classification
- [ ] Protocol plugins
- [ ] TX/replay (gated)
- [ ] Frontend integration

## Documentation

- [Gap Analysis](../../docs/RF/RF-GAP-ANALYSIS.md) - Feature comparison with FISSURE
- [Roadmap](../../docs/RF/RF-ROADMAP.md) - Implementation plan
- [Architecture](../../docs/RF/ARCHITECTURE.md) - System design (planned)
- [Drivers](../../docs/RF/DRIVERS.md) - SDR hardware setup (planned)
- [Security](../../docs/RF/SECURITY.md) - TX gating and RBAC (planned)
- [Legal](../../docs/RF/LEGAL.md) - Regulatory compliance (planned)

## Contributing

See main repository `CONTRIBUTING.md`. All RF work uses `feat:rf` label.

## License

MIT License - see repository `LICENSE` file.

**No GPL code was copied**. This is a clean-room implementation guided by public FISSURE documentation.

## References

- [FISSURE Project](https://github.com/ainfosec/FISSURE) (public docs only)
- [SigMF Specification](https://github.com/gnuradio/SigMF)
- [SoapySDR](https://github.com/pothosware/SoapySDR)
- [GNU Radio](https://wiki.gnuradio.org/)
- [vTOC Documentation](../../docs)

---

**Maintained by**: PR-CYBR vTOC RF Team  
**Status**: Active Development  
**Version**: 0.1.0
