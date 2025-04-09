import requests
from requests.auth import HTTPBasicAuth
import os
import csv
import logging


class Measurement:
    def __init__(self):
        self.base_url = f"https://api.sienge.com.br/{os.getenv("SUBDOMAIN")}/public/api/v1/"
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(os.getenv("USER"), os.getenv("PASSWORD"))

    def get_building_id_and_measurements(self, params: dict = None):
        building_url = f"{self.base_url}building-projects/progress-logs"
        response = self.session.get(url=building_url, params=params)

        logging.info(f"Response status code: {response.status_code}")
        logging.debug(f"Response content: {response.content}")
        if response.status_code == 200:
            try:
                data = response.json()
            except ValueError:
                print("Error: Response is not valid JSON.")
                return []
        else:
            print(f"Error: Received status code {response.status_code}")
            return []

        return [[item['buildingId'], item['measurementNumber']] for item in data['results']]

    def get_building_unit_id(self, params: dict = None):
        building_data = self.get_building_id_and_measurements()
        data = []

        for buildingId, measurementNumber in building_data:
            measurement_url = f"{self.base_url}building-projects/{buildingId}/progress-logs/{measurementNumber}"
            response = self.session.get(url=measurement_url, params=params)  
            if response.status_code == 200:
                try:
                    for buildingUnitId in response.json()["buildingUnits"]:
                        data.append([buildingId, measurementNumber, buildingUnitId['id']])
                except ValueError:
                    print(f"Error: Response for buildingId {buildingId} and measurementNumber {measurementNumber} is not valid JSON.")
            elif response.status_code == 404:
                data.append([0])
            else:
                print(f"Error: Received status code {response.status_code} for buildingId {buildingId} and measurementNumber {measurementNumber}")
            print(f"Response status code: {response.status_code}")
        return data


    def get_measurement_records(self,params: dict = None):
        records = self.get_building_unit_id()
        response_data = []
        for record in records:
            if len(record) == 3:
                building_id, measurement_number, building_unit_id = record
                records_url = f"{self.base_url}building-projects/{building_id}/progress-logs/{measurement_number}/items/{building_unit_id}"
                response = self.session.get(url=records_url, params=params)
                response_data.append(response.json())
                print(f"Response status code: {response.status_code}")
        return self.to_csv(response_data)


    def to_csv(self, csv_data):
        with open("output.csv", "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["taskId", "presentationId", "summary", "description",
                             "unitOfMeasure", "plannedQuantity", "measuredQuantity", "unitPrice",
                             "cumulativeMeasuredQuantity", "cumulativePercentage", "measureBalance"])
            for data in csv_data:
                for key, value in data.items():
                    if key == "results":
                        for r in value:
                            if type(r) == dict and r['taskId'] != 'next':
                                writer.writerow(r.values())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    initiate = Measurement()
    data = initiate.get_measurement_records()



