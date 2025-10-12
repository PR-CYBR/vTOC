import logging
import os
import requests

logger = logging.getLogger(__name__)

class MonitorAgent:
    """Agent for monitoring system health and metrics"""
    
    def __init__(self):
        self.api_url = os.getenv('API_URL', 'http://backend:8000')
        
    def run(self):
        """Run monitoring tasks"""
        logger.info("MonitorAgent: Starting monitoring cycle...")
        
        try:
            # Check API health
            response = requests.get(f"{self.api_url}/api/health", timeout=5)
            if response.status_code == 200:
                logger.info("MonitorAgent: API health check passed")
            else:
                logger.warning(f"MonitorAgent: API health check failed with status {response.status_code}")
            
            # Monitor operations
            operations = requests.get(f"{self.api_url}/api/operations/", timeout=5)
            if operations.status_code == 200:
                ops_data = operations.json()
                logger.info(f"MonitorAgent: Monitoring {len(ops_data)} operations")
                
                # Check for critical priority operations
                critical_ops = [op for op in ops_data if op.get('priority') == 'critical']
                if critical_ops:
                    logger.warning(f"MonitorAgent: Found {len(critical_ops)} critical priority operations")
            
            # Monitor agents status
            agents = requests.get(f"{self.api_url}/api/agents/", timeout=5)
            if agents.status_code == 200:
                agents_data = agents.json()
                running_agents = [a for a in agents_data if a.get('status') == 'running']
                logger.info(f"MonitorAgent: {len(running_agents)}/{len(agents_data)} agents running")
                
        except Exception as e:
            logger.error(f"MonitorAgent: Error during monitoring: {e}")
