import logging
import os
import requests

logger = logging.getLogger(__name__)

class AnalyzerAgent:
    """Agent for analyzing intelligence reports and mission data"""
    
    def __init__(self):
        self.api_url = os.getenv('API_URL', 'http://backend:8000')
        
    def run(self):
        """Run analysis tasks"""
        logger.info("AnalyzerAgent: Starting analysis cycle...")
        
        try:
            # Analyze intelligence reports
            intel = requests.get(f"{self.api_url}/api/intel/", timeout=5)
            if intel.status_code == 200:
                intel_data = intel.json()
                logger.info(f"AnalyzerAgent: Analyzing {len(intel_data)} intelligence reports")
                
                # Analyze by classification
                classifications = {}
                for report in intel_data:
                    classification = report.get('classification', 'unclassified')
                    classifications[classification] = classifications.get(classification, 0) + 1
                
                logger.info(f"AnalyzerAgent: Classification breakdown: {classifications}")
                
                # Check for high-priority intelligence
                verified_intel = [r for r in intel_data if r.get('reliability') == 'verified']
                if verified_intel:
                    logger.info(f"AnalyzerAgent: Found {len(verified_intel)} verified intelligence reports")
            
            # Analyze mission status
            missions = requests.get(f"{self.api_url}/api/missions/", timeout=5)
            if missions.status_code == 200:
                missions_data = missions.json()
                
                # Calculate mission statistics
                status_counts = {}
                for mission in missions_data:
                    status = mission.get('status', 'unknown')
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                logger.info(f"AnalyzerAgent: Mission status breakdown: {status_counts}")
                
        except Exception as e:
            logger.error(f"AnalyzerAgent: Error during analysis: {e}")
