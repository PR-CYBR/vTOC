"""SigMF metadata writer for RF Engine.

Implements SigMF (Signal Metadata Format) specification v1.x
https://github.com/gnuradio/SigMF

Clean-room implementation following public SigMF spec.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from loguru import logger

from ..config import settings


@dataclass
class SigMFGlobal:
    """SigMF global metadata section."""

    # Required core fields
    datatype: str  # e.g., "cf32_le" (complex float32 little-endian)
    sample_rate: float  # samples per second
    version: str = "1.0.0"
    
    # Optional core fields
    frequency: float | None = None  # center frequency when constant (Hz)
    hw: str | None = None  # hardware description
    description: str | None = None
    author: str | None = None
    license: str | None = None
    
    # PR-CYBR extensions
    prcybr_station_id: str | None = None
    prcybr_division: str | None = None
    prcybr_lat: float | None = None
    prcybr_lon: float | None = None


@dataclass
class SigMFCapture:
    """SigMF capture segment metadata."""

    sample_start: int  # sample index where capture starts
    frequency: float | None = None  # center frequency for this segment (Hz)
    datetime: str | None = None  # ISO 8601 timestamp
    
    # Optional fields
    global_index: int | None = None


@dataclass
class SigMFAnnotation:
    """SigMF annotation for signal identification."""

    sample_start: int  # start sample index
    sample_count: int  # number of samples
    
    # Optional fields
    freq_lower_edge: float | None = None  # Hz
    freq_upper_edge: float | None = None  # Hz
    label: str | None = None
    comment: str | None = None


class SigMFWriter:
    """Writes SigMF-compliant metadata files."""

    def __init__(self):
        """Initialize SigMF writer."""
        pass

    def create_metadata(
        self,
        datatype: str,
        sample_rate: float,
        center_freq_hz: float,
        hw_description: str,
        capture_datetime: datetime | None = None,
        station_id: str | None = None,
        division: str | None = None,
        lat: float | None = None,
        lon: float | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Create SigMF metadata structure.

        Args:
            datatype: Data type (e.g., "cf32_le")
            sample_rate: Sample rate in Hz
            center_freq_hz: Center frequency in Hz
            hw_description: Hardware description
            capture_datetime: Capture start time (default: now)
            station_id: Station identifier
            division: Division identifier
            lat: Latitude
            lon: Longitude
            description: Capture description

        Returns:
            SigMF metadata dictionary
        """
        if capture_datetime is None:
            capture_datetime = datetime.now(timezone.utc)

        # Build global section
        global_meta = {
            "core:datatype": datatype,
            "core:sample_rate": sample_rate,
            "core:version": "1.0.0",
        }

        # Add optional core fields
        if center_freq_hz is not None:
            global_meta["core:frequency"] = center_freq_hz

        if hw_description:
            global_meta["core:hw"] = hw_description

        if description:
            global_meta["core:description"] = description

        # Add PR-CYBR extensions
        if station_id or settings.prcybr_station_id:
            global_meta["prcybr:station_id"] = station_id or settings.prcybr_station_id

        if division or settings.prcybr_division:
            global_meta["prcybr:division"] = division or settings.prcybr_division

        if lat is not None:
            global_meta["prcybr:lat"] = lat

        if lon is not None:
            global_meta["prcybr:lon"] = lon

        # Build captures section
        captures = [
            {
                "core:sample_start": 0,
                "core:datetime": capture_datetime.isoformat() + "Z",
            }
        ]

        if center_freq_hz is not None:
            captures[0]["core:frequency"] = center_freq_hz

        # Build metadata structure
        metadata = {
            "global": global_meta,
            "captures": captures,
            "annotations": [],
        }

        return metadata

    def write_metadata_file(
        self,
        metadata: dict[str, Any],
        sigmf_path: str | Path,
    ) -> None:
        """Write SigMF metadata to .sigmf-meta file.

        Args:
            metadata: SigMF metadata dictionary
            sigmf_path: Path to .sigmf-meta file
        """
        sigmf_path = Path(sigmf_path)
        
        # Ensure .sigmf-meta extension
        if not sigmf_path.name.endswith(".sigmf-meta"):
            sigmf_path = sigmf_path.with_suffix(".sigmf-meta")

        # Create parent directory if needed
        sigmf_path.parent.mkdir(parents=True, exist_ok=True)

        # Write JSON
        with open(sigmf_path, "w") as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Wrote SigMF metadata: {sigmf_path}")

    def add_annotation(
        self,
        metadata: dict[str, Any],
        sample_start: int,
        sample_count: int,
        label: str | None = None,
        freq_lower_hz: float | None = None,
        freq_upper_hz: float | None = None,
        comment: str | None = None,
    ) -> dict[str, Any]:
        """Add annotation to SigMF metadata.

        Args:
            metadata: Existing metadata dictionary
            sample_start: Start sample index
            sample_count: Number of samples
            label: Signal label
            freq_lower_hz: Lower frequency edge (Hz)
            freq_upper_hz: Upper frequency edge (Hz)
            comment: Additional comment

        Returns:
            Updated metadata dictionary
        """
        annotation = {
            "core:sample_start": sample_start,
            "core:sample_count": sample_count,
        }

        if label:
            annotation["core:label"] = label

        if freq_lower_hz is not None:
            annotation["core:freq_lower_edge"] = freq_lower_hz

        if freq_upper_hz is not None:
            annotation["core:freq_upper_edge"] = freq_upper_hz

        if comment:
            annotation["core:comment"] = comment

        metadata["annotations"].append(annotation)
        return metadata

    def validate_metadata(self, metadata: dict[str, Any]) -> tuple[bool, list[str]]:
        """Validate SigMF metadata structure.

        Args:
            metadata: Metadata dictionary to validate

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []

        # Check top-level structure
        if "global" not in metadata:
            errors.append("Missing 'global' section")
        
        if "captures" not in metadata:
            errors.append("Missing 'captures' section")
        
        if "annotations" not in metadata:
            errors.append("Missing 'annotations' section")

        if errors:
            return False, errors

        # Validate global section
        global_meta = metadata["global"]
        required_fields = ["core:datatype", "core:sample_rate", "core:version"]
        
        for field in required_fields:
            if field not in global_meta:
                errors.append(f"Missing required field: {field}")

        # Validate captures section
        if not isinstance(metadata["captures"], list):
            errors.append("'captures' must be a list")
        elif len(metadata["captures"]) == 0:
            errors.append("'captures' list is empty")
        else:
            for i, capture in enumerate(metadata["captures"]):
                if "core:sample_start" not in capture:
                    errors.append(f"Capture {i} missing 'core:sample_start'")

        return len(errors) == 0, errors


# Global SigMF writer instance
sigmf_writer = SigMFWriter()
