import requests
import os
from dotenv import load_dotenv

load_dotenv()

host = os.getenv("HOST")
token_name = os.getenv("PROXMOX_TOKEN_NAME")
token_value = os.getenv("PROXMOX_TOKEN_VALUE")
port = os.getenv("PROXMOX_PORT", "8006")

url = f"https://{host}:{port}/api2/json/nodes"
headers = {
    "Authorization": f"PVEAPIToken={token_name}={token_value}"
}

print(f"URL: {url}")
print(f"Authorization: PVEAPIToken={token_name}=****")

try:
    response = requests.get(url, headers=headers, verify=False)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")