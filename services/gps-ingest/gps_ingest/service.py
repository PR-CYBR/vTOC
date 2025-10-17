"""Runtime service loop for ingesting GPS data."""

from __future__ import annotations

import json
import logging
import time
from contextlib import contextmanager
from typing import Callable, Iterable

import requests
import serial

from .config import Config
from .parser import GPSFix, parse_nmea_sentence

logger = logging.getLogger(__name__)

SerialFactory = Callable[..., serial.Serial]
SleepCallable = Callable[[float], None]


def connect_serial_with_retry(
    config: Config,
    serial_factory: SerialFactory,
    sleep: SleepCallable = time.sleep,
) -> serial.Serial:
    """Attempt to connect to the serial device with exponential backoff."""

    attempt = 0
    delay = max(config.reconnect_initial, 0)
    while True:
        try:
            logger.info(
                "Opening GPS serial connection on %s @ %s baud",
                config.serial_port,
                config.baud_rate,
            )
            connection = serial_factory(
                port=config.serial_port,
                baudrate=config.baud_rate,
                timeout=config.serial_timeout,
            )
            logger.info("GPS serial connection established")
            return connection
        except serial.SerialException as exc:
            attempt += 1
            logger.warning("GPS serial connection failed (attempt %s): %s", attempt, exc)
            if config.reconnect_max_attempts and attempt >= config.reconnect_max_attempts:
                raise
            sleep(delay)
            delay = min(max(delay * 2, 0.1), config.reconnect_max_delay)


class GPSIngestService:
    """High-level orchestration for streaming GPS fixes to the backend API."""

    def __init__(
        self,
        config: Config,
        serial_factory: SerialFactory = serial.Serial,
        session: requests.Session | None = None,
        sleep: SleepCallable = time.sleep,
    ) -> None:
        self.config = config
        self.serial_factory = serial_factory
        self.session = session or requests.Session()
        self.sleep = sleep

    @contextmanager
    def _serial_connection(self) -> Iterable[serial.Serial]:
        connection = connect_serial_with_retry(self.config, self.serial_factory, self.sleep)
        try:
            yield connection
        finally:
            try:
                connection.close()
            except serial.SerialException:
                logger.debug("Serial connection already closed")

    def publish_fix(self, fix: GPSFix) -> None:
        payload = fix.to_payload()
        logger.debug("Publishing GPS fix: %s", json.dumps(payload))
        response = self.session.post(
            self.config.api_url,
            json=payload,
            headers=self.config.headers,
            timeout=10,
        )
        response.raise_for_status()

    def run(self) -> None:
        """Run the ingestion loop until interrupted."""

        logger.info("Starting GPS ingestion service")
        try:
            while True:
                try:
                    with self._serial_connection() as connection:
                        self._stream(connection)
                except serial.SerialException as exc:
                    logger.warning("Serial connection lost: %s", exc)
                    self.sleep(self.config.reconnect_initial)
        except KeyboardInterrupt:
            logger.info("GPS ingestion interrupted; shutting down")
        finally:
            self.session.close()

    def _stream(self, connection: serial.Serial) -> None:
        while True:
            raw = connection.readline()
            if not raw:
                continue
            try:
                sentence = raw.decode("ascii", errors="ignore").strip()
            except UnicodeDecodeError:
                logger.debug("Received undecodable bytes from GPS receiver")
                continue
            fix = parse_nmea_sentence(sentence)
            if not fix:
                continue
            try:
                self.publish_fix(fix)
            except requests.RequestException as exc:
                logger.error("Failed to publish GPS fix: %s", exc)
                self.sleep(self.config.reconnect_initial)
                break
