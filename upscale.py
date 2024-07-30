import requests
import json
import time
import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Define the API endpoints and your API key
upscale_url = "https://api.apiframe.pro/upscale-1x"
fetch_url = "https://api.apiframe.pro/fetch"
api_key = os.getenv('API_KEY')  # API key from the .env file

# Check if the API key is available
if not api_key:
    raise ValueError("API key is not set in environment variables.")

# Define the payload for the upscale request
upscale_payload = json.dumps({
    "parent_task_id": "e863f070-fe24-4b92-9f01-6b57a9fa59ed",
    "index": "2"  # Assuming you want to upscale the second image
})

# Define the headers
headers = {
    'Content-Type': 'application/json',
    'Authorization': api_key
}

try:
    # Send the upscale request
    response = requests.post(upscale_url, headers=headers, data=upscale_payload)
    response.raise_for_status()  # Raise an error for bad responses
    upscale_response = response.json()

    # Extract the task_id from the response
    task_id = upscale_response.get("task_id")
    if not task_id:
        raise ValueError("No task_id returned in response.")
    print(f"Upscale Task ID: {task_id}")

    # Retry mechanism
    max_retries = 20
    retry_count = 0
    image_url = ""
    status = "processing"
    timeout = 600  # 10 minutes timeout

    start_time = time.time()

    while retry_count < max_retries and status == "processing" and (time.time() - start_time) < timeout:
        time.sleep(min(15 * (1.5 ** retry_count), 240))  # Exponential backoff, max 240 seconds

        # Define the payload for the fetch request
        fetch_payload = json.dumps({
            "task_id": task_id
        })

        # Send the fetch request
        fetch_response = requests.post(fetch_url, headers=headers, data=fetch_payload)
        fetch_response.raise_for_status()  # Raise an error for bad responses
        fetch_result = fetch_response.json()

        # Extract the status, percentage, and image URL from the fetch result
        status = fetch_result.get("status", "processing")
        percentage = fetch_result.get("percentage", "N/A")
        image_url = fetch_result.get("image_url", "")
        
        # Check the status of the task
        if status == "processing":
            print(f"Attempt {retry_count + 1}: Processing ({percentage}% complete). Waiting...")
        else:
            print("Upscaling completed.")
            break

        retry_count += 1

    # Print the upscaled image URL
    if image_url:
        print(f"Upscaled Image URL: {image_url}")
        
        # Save URL to a file
        with open('upscaled_image_url.txt', 'w') as f:
            f.write(f"Upscaled Image URL: {image_url}\n")
        print("Upscaled Image URL saved to upscaled_image_url.txt")
    else:
        print(f"Failed to retrieve upscaled image URL. Final status: {status}")
        print(f"Final response: {json.dumps(fetch_result, indent=2)}")

except requests.exceptions.RequestException as e:
    print(f"Request error: {e}")
    print(f"Response content: {e.response.content if e.response else 'No response content'}")
except ValueError as e:
    print(f"Value error: {e}")