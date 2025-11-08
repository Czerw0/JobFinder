'''This scripts i only for testing of api response structure
    It fetches data from the RemoteOK API and prints the structured JSON response.'''

import requests
import json
import sys


# The URL of the API endpoint 
API_URL = "https://remoteok.com/api"


HEADERS = {
    "User-Agent": "API-Inspector-Script/1.0"
}

def inspect_remoteok_api():
    """
    Fetches data from the RemoteOK API and prints the structured JSON response.
    """
    print(f"--- Contacting API endpoint: {API_URL} ---")

    try:
        # Make the GET request with a timeout to prevent it from hanging indefinitely.
        response = requests.get(API_URL, headers=HEADERS, timeout=20)

        # Raise an error for bad HTTP status codes (4xx or 5xx).
        response.raise_for_status()

    except requests.exceptions.HTTPError as e:
        print(f"\nHTTP Error: The server returned a status code {e.response.status_code}")
        print(f"   Reason: {e.response.reason}")
        print(f"   Response Text: {e.response.text}")
        sys.exit(1) # Exit with an error code
    except requests.exceptions.RequestException as e:
        # This catches network-related errors like timeouts, DNS errors, etc.
        print(f"\nNetwork Error: Could not connect to the API.")
        print(f"   Error Details: {e}")
        sys.exit(1)

    print(f"✅ Success! Received a response (Status Code: {response.status_code}).")
    print("--- Parsing JSON data... ---")

    try:
        # Try to parse the response text as JSON.
        data = response.json()
    except json.JSONDecodeError:
        print("\nJSON Error: The response from the API was not valid JSON.")
        print("--- Raw Response Text (first 500 characters) ---")
        print(response.text[:500])
        sys.exit(1)

    #response is ok, print some analysis
    print("\n--- API Response Analysis ---")
    if isinstance(data, list):
        print(f"The root of the JSON is a LIST containing {len(data)} items.")
        if data:
            # 2nd item is usually the first job offer (1st is legal notice)
            item_to_inspect = data[1] if len(data) > 1 else data[0]
            print("\nKeys found in the second item (a sample job offer):")
            for key in item_to_inspect.keys():
                print(f"  - {key}")
    elif isinstance(data, dict):
        print(f"The root of the JSON is a DICTIONARY (object) with {len(data)} keys.")
        print("\nKeys found in the dictionary:")
        for key in data.keys():
            print(f"  - {key}")
    else:
        print("The JSON is a single value (e.g., string, number).")

    # --- Full Pretty-Printed JSON Output ---
    print("\n--- Full JSON Response (Formatted) ---")
    # Use json.dumps to pretty-print the data with an indent of 2 spaces.
    pretty_json = json.dumps(data, indent=2)
    print(pretty_json)


if __name__ == "__main__":
    inspect_remoteok_api()