"""RF Engine for vTOC - FISSURE-class capabilities (MIT licensed, clean-room implementation).

This package provides Software Defined Radio (SDR) capabilities including:
- Device management (SoapySDR abstraction)
- IQ capture with SigMF metadata
- Signal classification (ML + heuristics)
- Protocol decoding (plugin architecture)
- Transmit/replay (gated with security controls)
- Archive and search
- WebSocket streaming (spectrum, IQ)

No GPL code was copied. Design is guided by public FISSURE documentation only.
"""

__version__ = "0.1.0"
__author__ = "PR-CYBR vTOC Team"
__license__ = "MIT"
