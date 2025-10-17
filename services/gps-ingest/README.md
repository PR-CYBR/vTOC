# GPS Ingest Service

The GPS ingest service opens a serial connection to a GPS receiver, parses NMEA
sentences, and forwards normalized position fixes to the vTOC backend API.

## Configuration

Configuration is provided via environment variables. The following variables are
required:

| Variable | Description |
| --- | --- |
| `GPS_SERIAL` | Serial device path (e.g. `/dev/ttyUSB0`). |
| `GPS_BAUD` | Optional baud rate for the GPS receiver (defaults to `9600`). |
| `GPS_API_URL` | Fully-qualified backend endpoint that accepts GPS fixes. |
| `GPS_API_TOKEN` | Optional bearer token for authenticating with the backend. |

Additional optional settings:

| Variable | Description |
| --- | --- |
| `GPS_RECONNECT_INITIAL` | Initial delay (seconds) before retrying serial connections (default `1.0`). |
| `GPS_RECONNECT_MAX_DELAY` | Maximum backoff delay (seconds) between retries (default `30.0`). |
| `GPS_RECONNECT_MAX_ATTEMPTS` | Maximum number of connection attempts before raising (unlimited by default). |
| `GPS_SERIAL_TIMEOUT` | Serial read timeout in seconds (default `1.0`). |

## Running locally

Install the service dependencies and execute the entrypoint:

```bash
pip install -e services/gps-ingest
GPS_SERIAL=/dev/ttyUSB0 \
GPS_API_URL=https://example.com/api/gps \
python -m gps_ingest
```

The service will continuously read sentences from the serial device, parse
position fixes, and POST JSON payloads to the configured API endpoint.

## Testing

Unit tests cover the NMEA parsing logic and serial connection retry behaviour.
Run them with:

```bash
pytest services/gps-ingest/tests
```

## Docker

A Dockerfile is provided for containerized deployments:

```bash
docker build -t vtoc-gps-ingest -f services/gps-ingest/Dockerfile .
docker run --rm \
  --device=/dev/ttyUSB0 \
  -e GPS_SERIAL=/dev/ttyUSB0 \
  -e GPS_API_URL=https://example.com/api/gps \
  -e GPS_API_TOKEN=your-token \
  vtoc-gps-ingest
```

Mount or pass the GPS serial device into the container using the `--device`
flag when running on Linux hosts.
