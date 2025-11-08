# RF Engine Implementation Roadmap

## Overview

This roadmap tracks the implementation of FISSURE-class RF capabilities in vTOC. All work follows clean-room design principles with no GPL code copying.

**Target**: Feature parity with FISSURE for RF operations within vTOC's MIT-licensed codebase.

## Epic Tracking

### Epic: RF Engine Core
**Labels**: `feat:rf`, `rf:engine`  
**Status**: 🟡 In Progress  
**Target**: 2024-12-15

- [ ] #TBD: RF Engine service skeleton
- [ ] #TBD: SoapySDR device abstraction
- [ ] #TBD: IQ capture with SigMF metadata
- [ ] #TBD: WebSocket spectrum streaming
- [ ] #TBD: Environment configuration

### Epic: RF Classification & Protocols
**Labels**: `feat:rf`, `rf:protocols`  
**Status**: ⚪ Planned  
**Target**: 2025-01-15

- [ ] #TBD: Spectrogram pipeline
- [ ] #TBD: ONNX classifier hooks
- [ ] #TBD: Protocol plugin architecture
- [ ] #TBD: OOK reference decoder
- [ ] #TBD: FSK reference decoder
- [ ] #TBD: IEEE 802.15.4 stub decoder

### Epic: RF Archive & Search
**Labels**: `feat:rf`, `rf:backend`  
**Status**: ⚪ Planned  
**Target**: 2025-02-01

- [ ] #TBD: Database schema for captures
- [ ] #TBD: S3/MinIO integration
- [ ] #TBD: SigMF indexer
- [ ] #TBD: Archive search API
- [ ] #TBD: Playlist system

### Epic: RF Frontend (Signal Lab)
**Labels**: `feat:rf`, `rf:frontend`  
**Status**: ⚪ Planned  
**Target**: 2025-02-15

- [ ] #TBD: Signal Lab route
- [ ] #TBD: Theme system (5 themes)
- [ ] #TBD: SpectrumPanel component
- [ ] #TBD: WaterfallPanel component
- [ ] #TBD: ConstellationPanel component
- [ ] #TBD: CaptureControl component
- [ ] #TBD: ArchiveBrowser component
- [ ] #TBD: DecoderPanel component
- [ ] #TBD: ReplayPanel component

### Epic: RF Transmit/Replay (Gated)
**Labels**: `feat:rf`, `rf:security`  
**Status**: ⚪ Planned  
**Target**: 2025-03-01

- [ ] #TBD: TX gating framework
- [ ] #TBD: Guard token system
- [ ] #TBD: Frequency whitelist enforcement
- [ ] #TBD: Replay pipeline
- [ ] #TBD: Audit logging
- [ ] #TBD: RBAC for RF_ADMIN role

### Epic: RF Agents & Automation
**Labels**: `feat:rf`, `rf:agents`  
**Status**: ⚪ Planned  
**Target**: 2025-03-15

- [ ] #TBD: RF agent task framework
- [ ] #TBD: rf_scan_band task
- [ ] #TBD: rf_triage task
- [ ] #TBD: ChatKit RF triggers
- [ ] #TBD: Agent telemetry integration

### Epic: RF Testing & CI
**Labels**: `feat:rf`, `rf:ci`  
**Status**: ⚪ Planned  
**Target**: 2025-04-01

- [ ] #TBD: IQ test fixtures
- [ ] #TBD: Unit tests (capture, classify, decode)
- [ ] #TBD: API integration tests
- [ ] #TBD: Frontend e2e tests
- [ ] #TBD: CI workflow updates
- [ ] #TBD: Container build/push

### Epic: RF Documentation
**Labels**: `feat:rf`, `rf:docs`  
**Status**: 🟡 In Progress  
**Target**: 2025-04-15

- [x] RF Gap Analysis
- [x] RF Roadmap (this document)
- [ ] #TBD: QUICKSTART.md
- [ ] #TBD: ARCHITECTURE.md
- [ ] #TBD: DRIVERS.md
- [ ] #TBD: PLAYLISTS.md
- [ ] #TBD: SECURITY.md
- [ ] #TBD: LEGAL.md
- [ ] #TBD: Example recipes

## Phase-by-Phase Breakdown

### Phase 0: Planning & Documentation ✅
**Duration**: 1 week  
**Status**: ✅ Complete

**Deliverables**:
- [x] Repository reconnaissance
- [x] `docs/RF/RF-GAP-ANALYSIS.md`
- [x] `docs/RF/RF-ROADMAP.md` (this document)
- [ ] GitHub issues with labels
- [ ] Epic tracking setup

**Success Criteria**:
- All stakeholders aligned on scope
- Architecture approved
- Issue backlog populated

---

### Phase 1: RF Engine Service Skeleton 🏗️
**Duration**: 1 week  
**Status**: ⚪ Not Started  
**Dependencies**: Phase 0

**Deliverables**:
- [ ] `services/rf-engine/` directory structure
- [ ] `pyproject.toml` with Poetry dependency management
- [ ] Minimal FastAPI app (`main.py`)
- [ ] Health endpoint (`/healthz`)
- [ ] Prometheus metrics endpoint (`/metrics`)
- [ ] Dockerfile (GNU Radio 3.10 base)
- [ ] `.env.example.rf`
- [ ] `README.md` with setup instructions
- [ ] Docker Compose integration

**File Structure**:
```
services/rf-engine/
├── rfengine/
│   ├── __init__.py
│   ├── main.py              # FastAPI app factory
│   ├── config.py            # Pydantic Settings
│   ├── devices/
│   │   └── __init__.py
│   ├── capture/
│   │   └── __init__.py
│   ├── replay/
│   │   └── __init__.py
│   ├── classify/
│   │   └── __init__.py
│   ├── protocols/
│   │   └── __init__.py
│   ├── archive/
│   │   └── __init__.py
│   ├── security/
│   │   └── __init__.py
│   ├── telemetry/
│   │   └── __init__.py
│   └── ws/
│       └── __init__.py
├── tests/
│   ├── __init__.py
│   └── fixtures/
├── pyproject.toml
├── Dockerfile
├── .env.example.rf
└── README.md
```

**Environment Variables**:
```bash
PRCYBR_STATION_ID=vtoc-001
PRCYBR_DIVISION=DIV-PR-001
RF_DEVICES_ALLOWLIST=rtlsdr,usrp,hackrf,limesdr
RF_TX_ENABLED=false
RF_TX_WHITELIST_FREQS_MHZ=
RF_SIGMF_ROOT=/data/sigmf
RF_S3_ENDPOINT=http://minio:9000
RF_S3_BUCKET=prcybr-rf
RF_S3_ACCESS_KEY=prcybr_rf_access
RF_S3_SECRET_KEY=REDACTED
RF_CLASSIFIER_MODEL_PATH=/models/spectro_cnn.onnx
RF_WS_SAMPLE_RATE_HZ=1000000
RF_WS_FFT_SIZE=2048
RF_MAX_CAPTURE_SECONDS=3600
```

**Success Criteria**:
- Service starts with `uvicorn rfengine.main:app`
- `/healthz` returns 200
- Docker build succeeds
- Service runs in Docker Compose stack

---

### Phase 2: Device Management & IQ Capture 📡
**Duration**: 2 weeks  
**Status**: ⚪ Not Started  
**Dependencies**: Phase 1

**Deliverables**:
- [ ] `rfengine/devices/manager.py` (SoapySDR wrapper)
- [ ] Device discovery and enumeration
- [ ] `rfengine/capture/rx_graph.py` (GNU Radio RX flowgraph)
- [ ] `rfengine/capture/sigmf_writer.py` (SigMF metadata)
- [ ] REST endpoints: `/api/v2/rf/devices/*`, `/api/v2/rf/capture/*`
- [ ] Unit tests with mock devices

**Key APIs**:
```python
# Device management
GET  /api/v2/rf/devices/list
POST /api/v2/rf/devices/{device_id}/test

# Capture control
POST /api/v2/rf/capture/start
POST /api/v2/rf/capture/stop
GET  /api/v2/rf/capture/status
```

**SigMF Metadata Requirements**:
- `core:datatype` (e.g., `cf32_le`)
- `core:sample_rate`
- `core:frequency`
- `core:hw`
- `prcybr:station_id`
- `prcybr:division`

**Success Criteria**:
- RTL-SDR detected and listed
- Capture starts and stops via API
- SigMF file written with correct metadata
- IQ data playback in GNU Radio Companion

---

### Phase 3: WebSocket Streaming & Visualization 📊
**Duration**: 1 week  
**Status**: ⚪ Not Started  
**Dependencies**: Phase 2

**Deliverables**:
- [ ] `rfengine/ws/psd_stream.py` (WebSocket PSD publisher)
- [ ] Server-side FFT pipeline
- [ ] Throttling and backpressure handling
- [ ] WebSocket endpoint: `/api/v2/rf/stream/psd`
- [ ] Integration tests with WebSocket client

**Protocol**:
```json
// Subscribe
{"action": "subscribe", "capture_id": "uuid", "fft_size": 2048}

// PSD Frame
{"type": "psd", "freq_mhz": [...], "power_db": [...], "timestamp": "ISO8601"}
```

**Success Criteria**:
- WebSocket connection established
- PSD frames received at 10+ Hz
- FFT visualization in test client

---

### Phase 4: Classification & Telemetry 🔍
**Duration**: 2 weeks  
**Status**: ⚪ Not Started  
**Dependencies**: Phase 2

**Deliverables**:
- [ ] `rfengine/classify/spectro.py` (spectrogram generator)
- [ ] `rfengine/classify/onnx_runner.py` (ONNX inference)
- [ ] Fallback energy/bandwidth heuristics
- [ ] Telemetry event emission
- [ ] REST endpoint: `/api/v2/rf/classify/run`

**Telemetry Schema**:
```python
{
  "event_type": "rf-detection",
  "station_id": "vtoc-001",
  "timestamp": "ISO8601",
  "freq_hz": 915000000,
  "span_hz": 200000,
  "snr_db": 12.5,
  "label": "ook_doorbell",
  "confidence": 0.87,
  "sigmf_uri": "s3://bucket/capture.sigmf"
}
```

**Success Criteria**:
- Spectrogram generated from IQ file
- ONNX model loaded (if present)
- Telemetry event emitted to backend
- Event visible in vTOC UI

---

### Phase 5: Protocol Plugin Framework 🔌
**Duration**: 2 weeks  
**Status**: ⚪ Not Started  
**Dependencies**: Phase 2

**Deliverables**:
- [ ] `rfengine/protocols/base.py` (abstract base class)
- [ ] Plugin discovery/registration system
- [ ] Reference decoders:
  - [ ] `ook_generic.py`
  - [ ] `fsk_generic.py`
  - [ ] `ieee802154_stub.py`
  - [ ] `lora_lite_stub.py`
- [ ] REST endpoints: `/api/v2/rf/protocol/decode`, `/api/v2/rf/protocol/craft`

**Plugin Interface**:
```python
class RFProtocol(ABC):
    name: str
    
    @abstractmethod
    def decode(self, sigmf_uri: str, **params) -> DecodedFrames:
        """Decode IQ to frames."""
        
    @abstractmethod
    def craft(self, fields: dict) -> IQFrame:
        """Craft IQ from fields."""
        
    def crc(self, bits: bytes) -> int:
        """Calculate CRC."""
```

**Success Criteria**:
- OOK decoder extracts bits from test fixture
- FSK decoder recovers clock and data
- Decoded frames displayed in JSON

---

### Phase 6: Archive & Search 🗄️
**Duration**: 1 week  
**Status**: ⚪ Not Started  
**Dependencies**: Phase 2

**Deliverables**:
- [ ] Database migration: `rf_captures` table
- [ ] `rfengine/archive/s3_adapter.py`
- [ ] SigMF indexer
- [ ] REST endpoints: `/api/v2/rf/archive/search`, `/api/v2/rf/archive/playlist`
- [ ] YAML playlist format

**Database Schema**:
```sql
CREATE TABLE rf_captures (
  id UUID PRIMARY KEY,
  station_id VARCHAR NOT NULL,
  started_at TIMESTAMPTZ NOT NULL,
  stopped_at TIMESTAMPTZ,
  center_freq_hz BIGINT NOT NULL,
  samp_rate BIGINT NOT NULL,
  path_uri TEXT NOT NULL,
  snr_avg_db FLOAT,
  labels TEXT[],
  latitude FLOAT,
  longitude FLOAT,
  division VARCHAR,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_rf_captures_freq ON rf_captures (center_freq_hz);
CREATE INDEX idx_rf_captures_time ON rf_captures (started_at);
CREATE INDEX idx_rf_captures_labels ON rf_captures USING GIN (labels);
```

**Success Criteria**:
- Capture indexed after completion
- Search by frequency range returns results
- Playlist created and stored

---

### Phase 7: Frontend Signal Lab 🎨
**Duration**: 2 weeks  
**Status**: ⚪ Not Started  
**Dependencies**: Phase 3, Phase 6

**Deliverables**:
- [ ] `frontend/src/pages/SignalLab.tsx`
- [ ] `frontend/src/theme/tokens.ts` (5 themes)
- [ ] `frontend/src/components/rf/SpectrumPanel.tsx`
- [ ] `frontend/src/components/rf/WaterfallPanel.tsx`
- [ ] `frontend/src/components/rf/ConstellationPanel.tsx`
- [ ] `frontend/src/components/rf/CaptureControl.tsx`
- [ ] `frontend/src/components/rf/ArchiveBrowser.tsx`
- [ ] `frontend/src/components/rf/DecoderPanel.tsx`
- [ ] Route: `/signal-lab`

**Theme Tokens**:
```typescript
{
  name: "NeoSynth",
  cssVars: {
    "--bg": "#0b0f14",
    "--panel": "#0f1621",
    "--grid": "rgba(255,255,255,0.06)",
    "--text": "#e6edf3",
    "--accent": "#00fff0",
    "--accent-2": "#ff2e88"
  }
}
```

**Success Criteria**:
- `/signal-lab` route loads
- Live spectrum visible
- Theme switcher works
- Capture controls functional

---

### Phase 8: Transmit/Replay (Gated) 🚨
**Duration**: 2 weeks  
**Status**: ⚪ Not Started  
**Dependencies**: Phase 2, Phase 6

**Deliverables**:
- [ ] `rfengine/security/tx_gatekeeper.py`
- [ ] Guard token issuance/validation
- [ ] Frequency whitelist enforcement
- [ ] `rfengine/replay/tx_graph.py` (GNU Radio TX flowgraph)
- [ ] Audit logging
- [ ] REST endpoints: `/api/v2/rf/replay/*`

**TX Gating Checks**:
1. `RF_TX_ENABLED=true` in environment
2. Frequency in `RF_TX_WHITELIST_FREQS_MHZ`
3. Valid `tx_guard_token` provided
4. User has `RF_ADMIN` role

**Audit Log**:
```python
{
  "event": "rf-tx-start",
  "user_id": "user123",
  "station_id": "vtoc-001",
  "timestamp": "ISO8601",
  "freq_hz": 915000000,
  "duration_s": 5.0,
  "sigmf_uri": "s3://bucket/replay.sigmf",
  "approved_by": "admin456"
}
```

**Success Criteria**:
- TX fails when `RF_TX_ENABLED=false`
- TX fails on non-whitelisted frequency
- TX succeeds with all 4 checks passed
- Audit log written

---

### Phase 9: RF Agents 🤖
**Duration**: 1 week  
**Status**: ⚪ Not Started  
**Dependencies**: Phase 4, Phase 5

**Deliverables**:
- [ ] `agents/rf-agent/tasks/scan_band.py`
- [ ] `agents/rf-agent/tasks/triage.py`
- [ ] `agents/rf-agent/tasks/replay_lab.py`
- [ ] ChatKit trigger configuration
- [ ] AgentKit playbook integration

**Agent Tasks**:
```python
# Automated band scan
rf_scan_band(division="DIV-PR-001", bandplan="ism_915")
  → Capture, classify, emit telemetry events

# Event triage
rf_triage(event_id="evt123")
  → Fetch SigMF, run decoders, update event

# Lab replay (requires RF_ADMIN)
rf_replay_lab(playlist_id="playlist456")
  → Execute playlist in sandbox
```

**Success Criteria**:
- Agent task runs on ChatKit trigger
- Band scan completes and emits events
- Triage updates event with decoded frames

---

### Phase 10: Testing & CI 🧪
**Duration**: 2 weeks  
**Status**: ⚪ Not Started  
**Dependencies**: All previous phases

**Deliverables**:
- [ ] IQ test fixtures (FM, OOK, FSK)
- [ ] Unit tests (pytest)
- [ ] API integration tests
- [ ] Frontend e2e tests (Playwright)
- [ ] CI workflow updates
- [ ] Container build/push
- [ ] Trivy security scan

**Test Coverage Targets**:
- Unit tests: >80%
- Integration tests: All endpoints
- E2e tests: Critical user flows

**Success Criteria**:
- CI passes on all test suites
- No security vulnerabilities in Trivy scan
- Images published to GHCR

---

### Phase 11: Documentation & Examples 📚
**Duration**: 1 week  
**Status**: ⚪ Not Started  
**Dependencies**: Phase 10

**Deliverables**:
- [ ] `docs/RF/QUICKSTART.md`
- [ ] `docs/RF/ARCHITECTURE.md`
- [ ] `docs/RF/DRIVERS.md`
- [ ] `docs/RF/PLAYLISTS.md`
- [ ] `docs/RF/SECURITY.md`
- [ ] `docs/RF/LEGAL.md`
- [ ] Example recipes:
  - [ ] ISM band scan
  - [ ] OOK doorbell capture/decode
  - [ ] SigMF playlist replay

**Success Criteria**:
- All docs complete and reviewed
- Example recipes tested
- Legal warnings in place

---

## Milestone Timeline

| Phase | Start Date | End Date | Status |
|-------|-----------|----------|--------|
| Phase 0: Planning | 2024-11-08 | 2024-11-15 | 🟡 In Progress |
| Phase 1: Skeleton | 2024-11-15 | 2024-11-22 | ⚪ Planned |
| Phase 2: Capture | 2024-11-22 | 2024-12-06 | ⚪ Planned |
| Phase 3: Streaming | 2024-12-06 | 2024-12-13 | ⚪ Planned |
| Phase 4: Classification | 2024-12-13 | 2024-12-27 | ⚪ Planned |
| Phase 5: Protocols | 2024-12-27 | 2025-01-10 | ⚪ Planned |
| Phase 6: Archive | 2025-01-10 | 2025-01-17 | ⚪ Planned |
| Phase 7: Frontend | 2025-01-17 | 2025-01-31 | ⚪ Planned |
| Phase 8: TX/Replay | 2025-01-31 | 2025-02-14 | ⚪ Planned |
| Phase 9: Agents | 2025-02-14 | 2025-02-21 | ⚪ Planned |
| Phase 10: Testing | 2025-02-21 | 2025-03-07 | ⚪ Planned |
| Phase 11: Docs | 2025-03-07 | 2025-03-14 | ⚪ Planned |

**Final Delivery Target**: 2025-03-14

## Risk Register

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| GNU Radio 3.10 compatibility issues | High | Medium | Test early with Docker container |
| SoapySDR driver stability | High | Medium | Vendor-specific fallbacks |
| Frontend performance (waterfall) | Medium | High | Use WebGL/Web Workers |
| TX gating circumvention | Critical | Low | Multi-layer checks + audit |
| License contamination (GPL) | Critical | Low | Code review + license scan |
| Hardware availability for testing | Medium | Medium | Mock devices + fixtures |

## Issue Labels

- `feat:rf` - RF feature work
- `rf:engine` - Backend RF engine
- `rf:frontend` - Signal Lab UI
- `rf:security` - TX gating, RBAC, audit
- `rf:docs` - Documentation
- `rf:ci` - CI/CD
- `rf:agents` - Agent integration
- `rf:protocols` - Protocol decoders

## Dependencies

### External Libraries
- GNU Radio 3.10
- SoapySDR + vendor drivers (rtl-sdr, uhd, hackrf, LimeSuite)
- numpy, scipy (DSP)
- sigmf (metadata)
- onnxruntime (classification)
- torch (optional, for training)
- prometheus-client (metrics)
- websockets (streaming)

### Internal Systems
- vTOC backend (`/api/v1/telemetry/*`)
- AgentKit task framework
- ChatKit webhook integration
- PostgreSQL with Alembic
- Docker/Swarm/Traefik

## Communication

- **Weekly Sync**: Thursday 10am ET
- **Issue Updates**: Tag `@pr-cybr/rf-team`
- **Slack Channel**: `#rf-engine`
- **Design Discussions**: GitHub Discussions (RF category)

---

**Last Updated**: 2025-11-08  
**Maintained By**: vTOC RF Team  
**License**: This document is part of vTOC (MIT License)
