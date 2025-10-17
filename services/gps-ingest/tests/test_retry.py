import itertools

import pytest
import serial

from gps_ingest.config import Config
from gps_ingest.service import connect_serial_with_retry


class DummySerial:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def close(self):
        pass


def test_connect_serial_with_retry_eventually_succeeds(monkeypatch):
    attempts = itertools.count()

    def factory(**kwargs):
        if next(attempts) < 2:
            raise serial.SerialException("boom")
        return DummySerial(**kwargs)

    sleep_calls = []

    def fake_sleep(delay):
        sleep_calls.append(delay)

    config = Config(
        serial_port="/dev/ttyUSB0",
        baud_rate=4800,
        api_url="https://example.com",
        api_token=None,
        reconnect_initial=0.1,
        reconnect_max_delay=0.5,
        reconnect_max_attempts=5,
    )

    conn = connect_serial_with_retry(config, factory, fake_sleep)

    assert isinstance(conn, DummySerial)
    assert sleep_calls == [0.1, 0.2]


def test_connect_serial_with_retry_respects_max_attempts():
    def factory(**kwargs):
        raise serial.SerialException("nope")

    config = Config(
        serial_port="/dev/ttyUSB0",
        baud_rate=4800,
        api_url="https://example.com",
        api_token=None,
        reconnect_initial=0.01,
        reconnect_max_delay=0.02,
        reconnect_max_attempts=3,
    )

    with pytest.raises(serial.SerialException):
        connect_serial_with_retry(config, factory, lambda _: None)
