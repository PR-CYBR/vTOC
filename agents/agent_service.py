import os
import time
import schedule
import logging
from modules.monitor_agent import MonitorAgent
from modules.analyzer_agent import AnalyzerAgent
from modules.executor_agent import ExecutorAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AgentService:
    """Main service for managing automation agents"""
    
    def __init__(self):
        self.agents = {
            'monitor': MonitorAgent(),
            'analyzer': AnalyzerAgent(),
            'executor': ExecutorAgent()
        }
        
    def start(self):
        """Start all agents"""
        logger.info("Starting Agent Service...")
        
        # Schedule agent tasks
        schedule.every(5).minutes.do(self.agents['monitor'].run)
        schedule.every(10).minutes.do(self.agents['analyzer'].run)
        schedule.every(15).minutes.do(self.agents['executor'].run)
        
        # Run immediately on startup
        for name, agent in self.agents.items():
            try:
                logger.info(f"Running {name} agent...")
                agent.run()
            except Exception as e:
                logger.error(f"Error running {name} agent: {e}")
        
        # Main loop
        logger.info("Agent Service started. Running scheduled tasks...")
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)
            except KeyboardInterrupt:
                logger.info("Shutting down Agent Service...")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(60)

if __name__ == "__main__":
    service = AgentService()
    service.start()
