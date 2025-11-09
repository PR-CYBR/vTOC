# RF Gap Analysis

## Executive Summary

This document analyzes the current vTOC capabilities against target FISSURE-class RF functionality. The goal is feature parity through clean-room implementation while maintaining MIT license compliance and avoiding any GPL code copying.

**License Context**: FISSURE is GPL-3.0. This analysis references FISSURE's public documentation and feature descriptions only—no source code is examined or copied.

## Current State (vTOC v1.0)

### Existing Capabilities
- ✅ FastAPI backend with modular service architecture
- ✅ Real-time telemetry ingestion and event pipeline
- ✅ Station management with role-based access
- ✅ Agent orchestration (ChatKit/AgentKit integration)
- ✅ Map-first frontend with React/Vite
- ✅ Docker/Swarm deployment with Traefik routing
- ✅ PostgreSQL with Alembic migrations
- ✅ ADS-B, GPS, H4M sensor integration
- ✅ WebSocket support for live data streams

### RF-Specific Gaps
- ❌ No SDR hardware abstraction layer
- ❌ No RF signal capture/storage
- ❌ No spectrum visualization
- ❌ No protocol decoding framework
- ❌ No signal classification
- ❌ No transmit/replay capabilities
- ❌ No RF-specific security controls

## Target State (FISSURE-Class RF Platform)

### Core RF Capabilities

| Capability | FISSURE Reference | vTOC Target | Priority | Complexity |
|------------|------------------|-------------|----------|------------|
| **SDR Device Support** | Multi-vendor SDR abstraction | SoapySDR-based device manager | P0 | Medium |
| **IQ Capture** | File writers with metadata | SigMF-compliant capture | P0 | Low |
| **Spectrum Visualization** | Live PSD/waterfall | WebSocket-based spectrum streaming | P0 | Medium |
| **Signal Classification** | ML-based modulation detection | ONNX/PyTorch inference hooks | P1 | High |
| **Protocol Decoding** | Plugin architecture for protocols | Modular decoder framework | P1 | High |
| **Transmit/Replay** | Gated TX with safety controls | Role-based TX with audit log | P2 | High |
| **Archive/Search** | Signal database with indexing | PostgreSQL + S3 archive | P1 | Medium |
| **Automation** | Scheduled scans and detection | Agent-driven RF workflows | P2 | Medium |

### Hardware Support Matrix

| Device | Interface | RX | TX | vTOC Status |
|--------|-----------|----|----|-------------|
| RTL-SDR | USB | ✓ | ✗ | Planned (RX only) |
| HackRF One | USB | ✓ | ✓ | Planned (gated TX) |
| USRP B/N/X Series | USB/Ethernet | ✓ | ✓ | Planned (gated TX) |
| LimeSDR | USB | ✓ | ✓ | Planned (gated TX) |
| BladeRF | USB | ✓ | ✓ | Optional |
| PlutoSDR | USB/Ethernet | ✓ | ✓ | Optional |

### Data Flow Architecture

```
┌──────────────┐
│ SDR Hardware │
└──────┬───────┘
       │ IQ samples
       ▼
┌──────────────┐
│ RF Engine    │──────────┐
│ (Capture)    │          │ SigMF
└──────┬───────┘          │
       │                  ▼
       │            ┌──────────────┐
       │            │ Archive      │
       │            │ (S3/MinIO)   │
       │            └──────────────┘
       ▼
┌──────────────┐
│ Classify     │
│ (ML/DSP)     │
└──────┬───────┘
       │ labels/confidence
       ▼
┌──────────────┐
│ Protocol     │
│ Decode       │
└──────┬───────┘
       │ decoded frames
       ▼
┌──────────────┐
│ Telemetry    │◄──────────┐
│ Events       │           │
└──────┬───────┘           │
       │                   │
       ▼                   │
┌──────────────┐           │
│ Backend API  │           │
└──────┬───────┘           │
       │                   │
       ▼                   │
┌──────────────┐    ┌──────┴───────┐
│ Frontend     │    │ Agents       │
│ Signal Lab   │    │ (RF tasks)   │
└──────────────┘    └──────────────┘
```

## Module-by-Module Delta

### 1. Device Management (`rfengine/devices/`)

**Current**: None  
**Target**: SoapySDR-based abstraction with discovery and capability detection

**Implementation Plan**:
- Create `DeviceManager` class wrapping SoapySDR API
- Auto-discovery with hardware fingerprinting
- Capability probing (freq ranges, sample rates, antennas)
- Connection pooling and error recovery
- Allowlist enforcement (env-based device filtering)

**Key APIs**:
```python
POST /api/v2/rf/devices/list
  Response: [{device_id, type, serial, rx_range, tx_range, available}]

POST /api/v2/rf/devices/{device_id}/test
  Response: {status, error}
```

**Dependencies**: SoapySDR, pyrtlsdr, uhd, libhackrf

### 2. IQ Capture (`rfengine/capture/`)

**Current**: None  
**Target**: Streaming capture with SigMF metadata generation

**Implementation Plan**:
- GNU Radio flowgraph wrappers
- Real-time file sinks with rotation
- SigMF metadata writer (core + PR-CYBR extensions)
- Bandwidth and duration limits
- WebSocket preview streams (decimated)

**Key APIs**:
```python
POST /api/v2/rf/capture/start
  Body: {device_id, freq_hz, samp_rate, bw_hz, gain_db, duration_s, lat?, lon?}
  Response: {capture_id, status, sigmf_uri}

POST /api/v2/rf/capture/stop
  Body: {capture_id}
  
GET /api/v2/rf/capture/status
  Query: capture_id
  Response: {capture_id, state, samples_captured, sigmf_uri}
```

**SigMF Required Fields**:
- `core:datatype` (e.g., `cf32_le`)
- `core:sample_rate`
- `core:frequency` (center when constant)
- `core:hw` (device description)
- `prcybr:station_id`
- `prcybr:division`

### 3. Classification (`rfengine/classify/`)

**Current**: None  
**Target**: Spectrogram-based signal classification with ML hooks

**Implementation Plan**:
- IQ → spectrogram pipeline (numpy/scipy)
- ONNX runtime for pre-trained models
- Fallback heuristics (energy detection, bandwidth estimation)
- Confidence thresholding
- Integration with telemetry events

**Key APIs**:
```python
POST /api/v2/rf/classify/run
  Body: {sigmf_uri | preview_buffer_id, model?, top_k?, threshold?}
  Response: {labels: [{name, confidence, freq_hz, bw_hz}]}
```

**Telemetry Integration**:
- Emit `rf-detection` events when confidence > threshold
- Include station location, frequency, SNR, label

### 4. Protocol Decoding (`rfengine/protocols/`)

**Current**: None  
**Target**: Plugin architecture with reference decoders

**Implementation Plan**:
- Abstract base class `RFProtocol`
- Plugin discovery/registration
- Reference implementations:
  - OOK (on-off keying) with CRC
  - FSK (frequency-shift keying) with clock recovery
  - IEEE 802.15.4 stub (frame structure only, no PHY)
  - LoRa Lite stub (symbol extraction demo)
- Decoder output: JSON frames with timestamps
- Optional Wireshark dissector generation

**Key APIs**:
```python
POST /api/v2/rf/protocol/decode
  Body: {sigmf_uri, plugin, params}
  Response: {frames: [{timestamp, data, crc_ok, fields}]}

POST /api/v2/rf/protocol/craft
  Body: {plugin, fields, center_freq_hz, samp_rate, tx_guard_token}
  Response: {iq_buffer_id, duration_samples}
```

**Security**: Craft requires `RF_TX_ENABLED=true` + valid token

### 5. Replay/Injection (`rfengine/replay/`)

**Current**: None  
**Target**: Sandboxed transmit with multi-layer gating

**Implementation Plan**:
- GNU Radio TX flowgraphs
- Gating checks:
  1. `RF_TX_ENABLED` env must be `true`
  2. Frequency must be in `RF_TX_WHITELIST_FREQS_MHZ`
  3. Valid `tx_guard_token` required (ephemeral, RBAC-issued)
  4. User must have `RF_ADMIN` role
- Amplitude limiting and PA protection
- Full audit trail (who, when, freq, duration)
- Playlist replay with scheduling

**Key APIs**:
```python
POST /api/v2/rf/replay/start
  Body: {sigmf_uri, center_freq_hz, samp_rate, gain_db, scale, tx_guard_token}
  Response: {replay_id, status, warnings}

POST /api/v2/rf/replay/stop
  Body: {replay_id}
```

**Audit Log Fields**: user_id, station_id, timestamp, freq_hz, duration_s, sigmf_uri, approved_by

### 6. Archive (`rfengine/archive/`)

**Current**: PostgreSQL for telemetry events  
**Target**: SigMF indexing with S3/MinIO backend

**Implementation Plan**:
- PostgreSQL table `rf_captures`:
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
    division VARCHAR
  );
  ```
- S3/MinIO adapter for binary IQ storage
- SigMF metadata colocated with .sigmf-data files
- Search/filter by band, time, label, SNR, location
- YAML playlist format:
  ```yaml
  name: ISM Band Survey
  items:
    - sigmf: s3://bucket/capture1.sigmf
      start: 0
      duration: 10.0
      loops: 1
      tx: false
  ```

**Key APIs**:
```python
GET /api/v2/rf/archive/search
  Query: ?band_mhz=915&label=ook&start_time=2024-01-01

POST /api/v2/rf/archive/playlist
  Body: {name, items}
  Response: {playlist_id}
```

### 7. Security (`rfengine/security/`)

**Current**: Basic RBAC for backend APIs  
**Target**: RF-specific RBAC + TX gating + audit logging

**Implementation Plan**:
- New roles:
  - `RF_ADMIN`: Full TX + replay
  - `RF_ANALYST`: RX + analysis
  - `OPS`/`INTEL`: View only
- TX guard token issuance with expiry
- Per-action audit logs shipped to Loki/ELK
- Rate limiting on capture/classify endpoints
- Device ownership tracking

**Security Defaults**:
- `RF_TX_ENABLED=false` out of the box
- Empty TX whitelist (no frequencies allowed)
- Require explicit user acknowledgment to enable TX

### 8. Telemetry Integration (`rfengine/telemetry/`)

**Current**: Generic telemetry event schema  
**Target**: RF-specific event types

**Implementation Plan**:
- Extend telemetry schema with RF fields:
  ```python
  event_type: "rf-detection" | "rf-capture-start" | "rf-capture-stop" | "rf-tx-start" | "rf-tx-stop"
  freq_hz: int
  span_hz: int
  snr_db: float
  label: str
  confidence: float
  sigmf_uri: str
  ```
- Emit events to existing `POST /api/v1/telemetry/rf-event`
- Agent hooks for anomaly detection

### 9. WebSocket Streaming (`rfengine/ws/`)

**Current**: None  
**Target**: Live PSD/IQ/constellation streaming

**Implementation Plan**:
- WebSocket endpoint `/api/v2/rf/stream/psd`
- Subscribe to capture_id or device_id
- Server-side decimation and FFT
- Throttled IQ preview (for constellation)
- Backpressure handling

**Protocol**:
```json
// Client → Server
{"action": "subscribe", "capture_id": "uuid", "fft_size": 2048, "decim": 10}

// Server → Client (PSD)
{"type": "psd", "timestamp": "ISO8601", "freq_mhz": [902, 902.1, ...], "power_db": [-80, -79, ...]}

// Server → Client (IQ)
{"type": "iq", "samples": [[0.1, 0.2], [0.3, -0.1], ...]}
```

### 10. Frontend Signal Lab (`frontend/src/pages/SignalLab.tsx`)

**Current**: Map-first UI  
**Target**: Dedicated RF analysis page

**Implementation Plan**:
- New route `/signal-lab` (lazy-loaded)
- Components:
  - `SpectrumPanel`: Live FFT plot (canvas-based)
  - `WaterfallPanel`: Scrolling spectrogram (WebGL or canvas)
  - `ConstellationPanel`: IQ scatter plot
  - `CaptureControl`: Device selector, freq/rate inputs, start/stop
  - `ArchiveBrowser`: SigMF search/preview
  - `DecoderPanel`: Plugin selector + frame table
  - `ReplayPanel`: Playlist manager + gated TX controls
- Theme system (5 themes) via CSS custom properties
- RBAC-aware UI (hide TX controls for non-admins)

**Theme Names**:
1. **NeoSynth**: Dark teal accents
2. **Dark Grid**: Subtle grid overlay
3. **CyberFlux**: Gradient purple-cyan
4. **NoirMesh**: Graphite with amber
5. **Retrowave Horizon**: Sunset gradient

### 11. Agent Integration (`agents/rf-agent/`)

**Current**: AgentKit tasks for telemetry  
**Target**: RF-specific agent tasks

**Implementation Plan**:
- `rf_scan_band(division, bandplan)`: Automated band sweep
- `rf_triage(event_id)`: Fetch SigMF, run decoders, update event
- `rf_replay_lab(playlist_id)`: Lab-only replay (requires RF_ADMIN)
- ChatKit trigger: "RF anomaly detected" → agent checklist

## Security & Compliance Considerations

### License Hygiene
- ✅ vTOC is MIT licensed
- ✅ No FISSURE code will be copied (FISSURE is GPL-3.0)
- ✅ Clean-room design guided by public documentation only
- ✅ All dependencies verified as MIT/BSD/Apache-2.0 compatible

### Regulatory Compliance
- 🔒 Default RX-only mode
- 🔒 TX requires explicit enabling + whitelist + role + token
- 🔒 All TX operations audited with operator identity
- 🔒 Documentation includes regulatory warnings
- 🔒 Example recipes focus on RX-only use cases

### Operational Security
- 🔒 Container runs as non-root
- 🔒 No new privileges (`security_opt: ["no-new-privileges:true"]`)
- 🔒 Capability drop (`cap_drop: [ALL]`)
- 🔒 Secrets via env vars (never committed)
- 🔒 Signed container images
- 🔒 Trivy vulnerability scanning in CI

## Implementation Phases

### Phase 0: Planning (Complete)
- [x] Gap analysis document
- [ ] Roadmap document
- [ ] GitHub issues created

### Phase 1: RF Engine Skeleton (Week 1)
- [ ] Service structure
- [ ] Docker build
- [ ] Health endpoint
- [ ] Environment config

### Phase 2: Core RX (Week 2)
- [ ] Device manager
- [ ] IQ capture
- [ ] SigMF writer
- [ ] WebSocket PSD

### Phase 3: Classification (Week 3)
- [ ] Spectrogram pipeline
- [ ] ONNX hooks
- [ ] Telemetry events

### Phase 4: Protocol Framework (Week 4)
- [ ] Plugin architecture
- [ ] OOK/FSK/802.15.4 stubs

### Phase 5: Archive (Week 5)
- [ ] Database schema
- [ ] S3 adapter
- [ ] Search API

### Phase 6: Frontend (Week 6)
- [ ] Signal Lab page
- [ ] Spectrum/waterfall
- [ ] Theme system

### Phase 7: TX/Replay (Week 7)
- [ ] Gated TX pipeline
- [ ] Audit logging
- [ ] Playlist replay

### Phase 8: Agents (Week 8)
- [ ] RF agent tasks
- [ ] ChatKit integration

### Phase 9: Testing & CI (Week 9)
- [ ] Unit tests
- [ ] Integration tests
- [ ] CI workflows

### Phase 10: Documentation (Week 10)
- [ ] User guides
- [ ] API reference
- [ ] Example recipes

## Success Metrics

- ✅ RTL-SDR capture to SigMF with metadata
- ✅ Live spectrum visible in `/signal-lab`
- ✅ Capture indexed and searchable
- ✅ At least 2 protocol decoders functional
- ✅ TX gating verified (requires all 4 checks)
- ✅ No GPL code in repository
- ✅ CI green
- ✅ Security audit passed

## References

- [FISSURE Project Documentation](https://github.com/ainfosec/FISSURE) (public docs only, no code examined)
- [SigMF Specification](https://github.com/gnuradio/SigMF)
- [SoapySDR API](https://github.com/pothosware/SoapySDR/wiki)
- [GNU Radio 3.10 Documentation](https://wiki.gnuradio.org/)
- [vTOC Architecture](../ARCHITECTURE.md)

---

**Last Updated**: 2025-11-08  
**Maintained By**: vTOC RF Team  
**License**: This document is part of vTOC (MIT License)
