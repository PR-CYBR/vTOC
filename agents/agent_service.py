import os
import time
from pathlib import Path
from typing import Any, Callable, Dict

import logging
import schedule
import yaml

from modules.monitor_agent import MonitorAgent
from modules.analyzer_agent import AnalyzerAgent
from modules.executor_agent import ExecutorAgent
from modules.sources import (
    ADSBSourceConnector,
    AISSourceConnector,
    APRSSourceConnector,
    TLESourceConnector,
    RTLSDRSourceConnector,
    MeshtasticSourceConnector,
    GPSSourceConnector,
)
from modules.sources.base import TelemetrySourceConnector


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


SOURCE_REGISTRY: Dict[str, Callable[[str, Dict[str, Any]], TelemetrySourceConnector]] = {
    "adsb": ADSBSourceConnector,
    "ais": AISSourceConnector,
    "aprs": APRSSourceConnector,
    "tle": TLESourceConnector,
    "rtlsdr": RTLSDRSourceConnector,
    "meshtastic": MeshtasticSourceConnector,
    "gps": GPSSourceConnector,
}


class AgentService:
    """Main service for managing automation agents and telemetry sources."""

    def __init__(self, config_path: str | None = None):
        self.config_path = Path(
            config_path or os.getenv("AGENT_CONFIG_PATH", "config/agents.yml")
        )
        self.config = self._load_config()
        self.agents = self._initialize_agents()
        self.source_connectors = self._initialize_sources()
        self.startup_jobs: list[Callable[[], None]] = []

    def _load_config(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            logger.warning("Agent configuration not found at %s", self.config_path)
            return {}

        with self.config_path.open("r", encoding="utf-8") as stream:
            data = yaml.safe_load(stream) or {}
            logger.debug("Loaded agent configuration: %s", data)
            return data

    def _initialize_agents(self) -> Dict[str, Any]:
        agents_config = self.config.get("agents", {})
        agents: Dict[str, Any] = {}

        if agents_config.get("monitor", {}).get("enabled", True):
            agents["monitor"] = MonitorAgent()
        if agents_config.get("analyzer", {}).get("enabled", True):
            agents["analyzer"] = AnalyzerAgent()
        if agents_config.get("executor", {}).get("enabled", True):
            agents["executor"] = ExecutorAgent()

        return agents

    def _initialize_sources(self) -> Dict[str, TelemetrySourceConnector]:
        sources_config = self.config.get("sources", {})
        connectors: Dict[str, TelemetrySourceConnector] = {}

        for source_slug, source_config in sources_config.items():
            if not source_config.get("enabled", True):
                logger.info("Telemetry source %s disabled in configuration", source_slug)
                continue

            source_type = source_config.get("type", source_slug).lower()
            connector_cls = SOURCE_REGISTRY.get(source_type)
            if not connector_cls:
                logger.warning("Unknown telemetry source type '%s'", source_type)
                continue

            connector = connector_cls(source_slug, source_config)
            connectors[source_slug] = connector
            self._schedule_source(source_slug, connector, source_config)

        return connectors

    @staticmethod
    def _parse_interval(schedule_value: Any, default_minutes: int = 5) -> tuple[str, int]:
        if isinstance(schedule_value, (int, float)) and schedule_value > 0:
            return "minutes", int(schedule_value)

        if isinstance(schedule_value, str):
            value = schedule_value.strip()
            if value.startswith("*/"):
                try:
                    minutes = int(value.split()[0][2:])
                    return "minutes", max(1, minutes)
                except (ValueError, IndexError):
                    logger.debug("Unable to parse cron expression %s", value)
            if value.endswith("s"):
                try:
                    seconds = int(value[:-1])
                    return "seconds", max(1, seconds)
                except ValueError:
                    logger.debug("Unable to parse seconds expression %s", value)
            if value.endswith("m"):
                try:
                    minutes = int(value[:-1])
                    return "minutes", max(1, minutes)
                except ValueError:
                    logger.debug("Unable to parse minutes expression %s", value)

        return "minutes", default_minutes

    def _schedule_job(self, label: str, job: Callable[[], None], schedule_value: Any) -> None:
        unit, interval = self._parse_interval(schedule_value)
        if unit == "seconds":
            schedule.every(interval).seconds.do(job)
        else:
            schedule.every(interval).minutes.do(job)
        self.startup_jobs.append(job)
        logger.info("Scheduled %s every %d %s", label, interval, unit)

    def _schedule_source(
        self,
        source_slug: str,
        connector: TelemetrySourceConnector,
        source_config: Dict[str, Any],
    ) -> None:
        schedule_value = source_config.get("schedule", 5)

        def job() -> None:
            logger.info("Polling telemetry source %s", source_slug)
            payload = connector.poll()
            if payload:
                connector.push_event(payload)

        self._schedule_job(f"source:{source_slug}", job, schedule_value)

    def start(self) -> None:
        """Start all agents and source polling."""
        logger.info("Starting Agent Service...")

        agents_config = self.config.get("agents", {})

        for name, agent in self.agents.items():
            schedule_value = agents_config.get(name, {}).get("schedule", 5)

            def make_job(agent_name: str, agent_instance: Any) -> Callable[[], None]:
                def _job() -> None:
                    logger.info("Running %s agent", agent_name)
                    agent_instance.run()

                return _job

            job = make_job(name, agent)
            self._schedule_job(f"agent:{name}", job, schedule_value)

        logger.info("Agent Service started. Running scheduled tasks...")

        for job in self.startup_jobs:
            try:
                job()
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.error("Startup execution failed: %s", exc)

        while True:
            try:
                schedule.run_pending()
                time.sleep(60)
            except KeyboardInterrupt:
                logger.info("Shutting down Agent Service...")
                break
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.error("Error in main loop: %s", exc)
                time.sleep(60)


if __name__ == "__main__":
    service = AgentService()
    service.start()

