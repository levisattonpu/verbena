import requests
from requests.auth import HTTPBasicAuth
import os
import csv
import logging
from typing import List, Dict, Optional, Union
from dataclasses import dataclass


@dataclass
class MeasurementConfig:
    subdomain: str = os.getenv("SUBDOMAIN", "")
    user: str = os.getenv("USER", "")
    password: str = os.getenv("PASSWORD", "")


class APIError(Exception):
    """Custom exception for API errors"""
    pass


class Measurement:
    def __init__(self, config: MeasurementConfig = None):
        self.config = config or MeasurementConfig()
        self.base_url = f"https://api.sienge.com.br/{self.config.subdomain}/public/api/v1/"
        self.session = self._create_session()
        self.logger = logging.getLogger(__name__)

    def _create_session(self) -> requests.Session:
        """Create and configure requests session"""
        session = requests.Session()
        session.auth = HTTPBasicAuth(self.config.user, self.config.password)
        session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        return session

    def _make_request(self, url: str, params: Optional[dict] = None) -> Union[dict, list]:
        """Generic request handler with error handling"""
        try:
            response = self.session.get(url, params=params)
            self.logger.debug(f"Request to {url} - Status: {response.status_code}")
            
            if response.status_code != 200:
                self.logger.error(f"API request failed. Status: {response.status_code}, Response: {response.text}")
                raise APIError(f"API request failed with status {response.status_code}")

            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed: {str(e)}")
            raise APIError(f"Request failed: {str(e)}")
        except ValueError as e:
            self.logger.error(f"Invalid JSON response: {str(e)}")
            raise APIError("Invalid JSON response")

    def get_building_projects(self, params: Optional[dict] = None) -> List[Dict]:
        """Get all building projects with their measurements"""
        url = f"{self.base_url}building-projects/progress-logs"
        try:
            data = self._make_request(url, params)
            return data.get('results', [])
        except APIError:
            return []

    def get_building_units(self, building_id: str, measurement_number: str) -> List[Dict]:
        """Get units for a specific building project and measurement"""
        url = f"{self.base_url}building-projects/{building_id}/progress-logs/{measurement_number}"
        try:
            data = self._make_request(url)
            return data.get('buildingUnits', [])
        except APIError:
            return []

    def get_measurement_records(self, building_id: str, measurement_number: str, building_unit_id: str) -> List[Dict]:
        """Get measurement records for a specific building unit"""
        url = f"{self.base_url}building-projects/{building_id}/progress-logs/{measurement_number}/items/{building_unit_id}"
        try:
            data = self._make_request(url)
            return data.get('results', [])
        except APIError:
            return []

    def export_all_measurements_to_csv(self, output_file: str = "measurements.csv", params: Optional[dict] = None) -> bool:
        """Main method to export all measurements data to CSV"""
        try:
            with open(output_file, "w", newline="", encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=[
                    "taskId", "presentationId", "summary", "description",
                    "unitOfMeasure", "plannedQuantity", "measuredQuantity", 
                    "unitPrice", "cumulativeMeasuredQuantity", 
                    "cumulativePercentage", "measureBalance"
                ])
                writer.writeheader()

                buildings = self.get_building_projects(params)
                for building in buildings:
                    building_id = building.get('buildingId')
                    measurement_number = building.get('measurementNumber')
                    
                    units = self.get_building_units(building_id, measurement_number)
                    for unit in units:
                        unit_id = unit.get('id')
                        records = self.get_measurement_records(building_id, measurement_number, unit_id)
                        
                        for record in records:
                            if isinstance(record, dict) and record.get('taskId') != 'next':
                                writer.writerow(record)
            
            self.logger.info(f"Successfully exported data to {output_file}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to export data: {str(e)}")
            return False


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('measurement_export.log')
        ]
    )

    try:
        measurement = Measurement()
        success = measurement.export_all_measurements_to_csv()
        if not success:
            logging.error("Measurement export failed")
            exit(1)
    except Exception as e:
        logging.critical(f"Application failed: {str(e)}")
        exit(1)