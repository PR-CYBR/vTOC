"""Tests for SigMF metadata writer."""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from rfengine.capture.sigmf import SigMFWriter


@pytest.fixture
def sigmf_writer():
    """Create SigMF writer."""
    return SigMFWriter()


def test_create_metadata_minimal(sigmf_writer):
    """Test creating minimal SigMF metadata."""
    metadata = sigmf_writer.create_metadata(
        datatype="cf32_le",
        sample_rate=2.4e6,
        center_freq_hz=915e6,
        hw_description="RTL-SDR Generic",
    )

    assert "global" in metadata
    assert "captures" in metadata
    assert "annotations" in metadata

    # Check required global fields
    global_meta = metadata["global"]
    assert global_meta["core:datatype"] == "cf32_le"
    assert global_meta["core:sample_rate"] == 2.4e6
    assert global_meta["core:version"] == "1.0.0"
    assert global_meta["core:frequency"] == 915e6
    assert global_meta["core:hw"] == "RTL-SDR Generic"

    # Check captures
    assert len(metadata["captures"]) == 1
    assert metadata["captures"][0]["core:sample_start"] == 0
    assert metadata["captures"][0]["core:frequency"] == 915e6
    assert "core:datetime" in metadata["captures"][0]

    # Check annotations
    assert isinstance(metadata["annotations"], list)


def test_create_metadata_with_extensions(sigmf_writer):
    """Test creating metadata with PR-CYBR extensions."""
    metadata = sigmf_writer.create_metadata(
        datatype="cf32_le",
        sample_rate=2.4e6,
        center_freq_hz=915e6,
        hw_description="HackRF One",
        station_id="test-station",
        division="DIV-TEST",
        lat=18.4655,
        lon=-66.1057,
        description="Test capture",
    )

    global_meta = metadata["global"]
    assert global_meta["prcybr:station_id"] == "test-station"
    assert global_meta["prcybr:division"] == "DIV-TEST"
    assert global_meta["prcybr:lat"] == 18.4655
    assert global_meta["prcybr:lon"] == -66.1057
    assert global_meta["core:description"] == "Test capture"


def test_write_metadata_file(sigmf_writer):
    """Test writing metadata to file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        sigmf_path = Path(tmpdir) / "test.sigmf-meta"

        metadata = sigmf_writer.create_metadata(
            datatype="cf32_le",
            sample_rate=2.4e6,
            center_freq_hz=915e6,
            hw_description="Test Device",
        )

        sigmf_writer.write_metadata_file(metadata, sigmf_path)

        # Verify file exists
        assert sigmf_path.exists()

        # Verify content
        with open(sigmf_path) as f:
            loaded = json.load(f)

        assert loaded["global"]["core:datatype"] == "cf32_le"
        assert loaded["global"]["core:sample_rate"] == 2.4e6


def test_add_annotation(sigmf_writer):
    """Test adding annotations to metadata."""
    metadata = sigmf_writer.create_metadata(
        datatype="cf32_le",
        sample_rate=2.4e6,
        center_freq_hz=915e6,
        hw_description="Test Device",
    )

    # Add annotation
    metadata = sigmf_writer.add_annotation(
        metadata,
        sample_start=1000,
        sample_count=5000,
        label="ook_signal",
        freq_lower_hz=914.5e6,
        freq_upper_hz=915.5e6,
        comment="Detected OOK transmission",
    )

    assert len(metadata["annotations"]) == 1
    annotation = metadata["annotations"][0]
    assert annotation["core:sample_start"] == 1000
    assert annotation["core:sample_count"] == 5000
    assert annotation["core:label"] == "ook_signal"
    assert annotation["core:freq_lower_edge"] == 914.5e6
    assert annotation["core:freq_upper_edge"] == 915.5e6
    assert annotation["core:comment"] == "Detected OOK transmission"


def test_validate_metadata_valid(sigmf_writer):
    """Test validating valid metadata."""
    metadata = sigmf_writer.create_metadata(
        datatype="cf32_le",
        sample_rate=2.4e6,
        center_freq_hz=915e6,
        hw_description="Test Device",
    )

    is_valid, errors = sigmf_writer.validate_metadata(metadata)
    assert is_valid is True
    assert len(errors) == 0


def test_validate_metadata_missing_required(sigmf_writer):
    """Test validating metadata with missing required fields."""
    # Missing datatype
    metadata = {
        "global": {
            "core:sample_rate": 2.4e6,
            "core:version": "1.0.0",
        },
        "captures": [{"core:sample_start": 0}],
        "annotations": [],
    }

    is_valid, errors = sigmf_writer.validate_metadata(metadata)
    assert is_valid is False
    assert any("core:datatype" in err for err in errors)


def test_validate_metadata_missing_sections(sigmf_writer):
    """Test validating metadata with missing sections."""
    metadata = {"global": {}}

    is_valid, errors = sigmf_writer.validate_metadata(metadata)
    assert is_valid is False
    assert any("captures" in err for err in errors)
    assert any("annotations" in err for err in errors)
