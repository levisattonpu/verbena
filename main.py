import requests
from requests.auth import HTTPBasicAuth
import os



def get_measurements(params:dict = None):

    sienge_url = os.getenv("URL")
    sienge_user = os.getenv("USER")
    sienge_password = os.getenv("PASSWORD")
    
    auth = HTTPBasicAuth(sienge_user, sienge_password)
    response = requests.get(url=sienge_url, auth=auth, params=params)

    print(f"Response status code: {response.status_code}")
    print(f"Response content: {response.content}")
    
    return response.json()

if __name__ == "__main__":
    print(get_measurements())
    