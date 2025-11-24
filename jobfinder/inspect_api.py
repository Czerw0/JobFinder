'''
Quick script to check the structure of the RemoteOK API response.
It fetches the API data and prints a readable, formatted JSON so you can inspect keys and content.
'''

import requests
import json
import sys


# RemoteOK API endpoint
API_URL = "https://remoteok.com/api"


HEADERS = {
    "User-Agent": "API-Inspector-Script/1.0"
}

def inspect_remoteok_api():
    """
    Call the RemoteOK API, validate the response, and print a human-friendly analysis
    plus the full pretty-printed JSON.
    """
    print(f"Contacting API endpoint: {API_URL}")

    try:
        # Perform a GET request with a timeout so it doesn't hang forever.
        response = requests.get(API_URL, headers=HEADERS, timeout=20)

        # If the server responded with an error status, raise an exception.
        response.raise_for_status()

    except requests.exceptions.HTTPError as e:
        print(f"\nHTTP Error: The server returned a status code {e.response.status_code}")
        print(f"   Reason: {e.response.reason}")
        print(f"   Response Text: {e.response.text}")
        sys.exit(1)  # Exit with a non-zero code to indicate failure
    except requests.exceptions.RequestException as e:
        # Catches network-related problems like timeouts or DNS failures.
        print(f"\nNetwork Error: Could not connect to the API.")
        print(f"   Error Details: {e}")
        sys.exit(1)

    print(f"Success! Received a response (Status Code: {response.status_code}).")
    print("Parsing JSON data...")

    try:
        # Parse response body as JSON.
        data = response.json()
    except json.JSONDecodeError:
        print("\nJSON Error: The response from the API was not valid JSON.")
        print("Raw Response Text (first 500 characters)")
        print(response.text[:500])
        sys.exit(1)

    # Response parsed successfully — provide some quick analysis.
    print("\nAPI Response Analysis")
    if isinstance(data, list):
        print(f"The root of the JSON is a LIST containing {len(data)} items.")
        if data:
            # On RemoteOK, the first element is usually a notice; the second is the first job.
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

    # Inspecting the content
    print("\nFull JSON Response (Formatted)")
    pretty_json = json.dumps(data, indent=2)
    print(pretty_json)


if __name__ == "__main__":
    inspect_remoteok_api()