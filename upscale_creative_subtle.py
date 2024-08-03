import requests
import json
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API endpoints
upscale_url = "https://api.apiframe.pro/upscale-alt"
fetch_url = "https://api.apiframe.pro/fetch"

# Get API key from environment variable
api_key = os.getenv('API_KEY')

if not api_key:
    raise ValueError("API key is not set in environment variables.")

# Upscale request payload
upscale_payload = json.dumps({
    "parent_task_id": "f4750af5-3c42-41fd-9d81-b912c6ff7318",
    "type": "creative"
})

# Headers
headers = {
    'Content-Type': 'application/json',
    'Authorization': api_key
}

try:
    # Send upscale request
    response = requests.post(upscale_url, headers=headers, data=upscale_payload)
    response.raise_for_status()
    upscale_response = response.json()

    task_id = upscale_response.get("task_id")
    if not task_id:
        raise ValueError("No task_id returned in response.")
    print(f"Creative Upscale Task ID: {task_id}")

    # Polling for task completion
    max_retries = 30
    retry_count = 0
    status = "processing"
    timeout = 600  # 10 minutes timeout

    start_time = time.time()

    while retry_count < max_retries and status not in ["finished", "success"] and (time.time() - start_time) < timeout:
        time.sleep(min(10 * (1.2 ** retry_count), 60))  # Exponential backoff, max 60 seconds

        # Fetch request
        fetch_payload = json.dumps({"task_id": task_id})
        fetch_response = requests.post(fetch_url, headers=headers, data=fetch_payload)
        fetch_response.raise_for_status()
        fetch_result = fetch_response.json()

        status = fetch_result.get("status", "processing")
        percentage = fetch_result.get("percentage", "N/A")
        
        if status == "processing":
            print(f"Attempt {retry_count + 1}: Processing ({percentage}% complete). Waiting...")
        elif status in ["finished", "success"]:
            print("Creative upscaling completed.")
            break
        else:
            print(f"Unexpected status: {status}. Stopping retries.")
            break

        retry_count += 1

    # Check final result
    if status in ["finished", "success"]:
        image_url = fetch_result.get("image_url")
        task_type = fetch_result.get("task_type")
        print(f"Creative Upscaled Image URL: {image_url}")
        print(f"Task Type: {task_type}")
        
        # Save URL to a file
        with open('upscaled_subtle-creative_url.txt', 'w') as f:
            f.write(f"Upscaled Creative-Subtle Task ID: {task_id}\n")
            f.write(f"Creative Upscaled Image URL: {image_url}\n")
            f.write(f"Task Type: {task_type}\n")
        print("Creative Upscaled Image URL saved to upscaled_subtle-creative_url.txt")
    else:
        print(f"Failed to retrieve creative upscaled image. Final status: {status}")
        print(f"Final response: {json.dumps(fetch_result, indent=2)}")

except requests.exceptions.RequestException as e:
    print(f"Request error: {e}")
    if hasattr(e, 'response'):
        print(f"Response status code: {e.response.status_code}")
        print(f"Response content: {e.response.text}")
    else:
        print("No response available")
except json.JSONDecodeError as e:
    print(f"JSON decode error: {e}")
    print(f"Raw response content: {response.text}")
except ValueError as e:
    print(f"Value error: {e}")