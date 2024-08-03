import requests
import json
import time
import os
from dotenv import load_dotenv

load_dotenv()

imagine_url = "https://api.apiframe.pro/imagine"
fetch_url = "https://api.apiframe.pro/fetch"
api_key = os.getenv('API_KEY')

if not api_key:
    raise ValueError("API key is not set in environment variables.")

imagine_payload = json.dumps({
    "prompt": "A traditional Indian chef in authentic attire, carefully layering marinated chicken and fragrant basmati rice in a large copper pot. The chef's hands are seen sprinkling saffron-infused milk over the dish, highlighting the meticulous preparation process.",
    "aspect_ratio": "3:2",
    "webhook_url": "",
    "webhook_secret": ""
})

headers = {
    'Content-Type': 'application/json',
    'Authorization': api_key
}

try:
    response = requests.post(imagine_url, headers=headers, data=imagine_payload)
    response.raise_for_status()
    imagine_response = response.json()

    task_id = imagine_response.get("task_id")
    if not task_id:
        raise ValueError("No task_id returned in response.")
    print(f"Task ID: {task_id}")

    max_retries = 20
    retry_count = 0
    image_urls = []
    original_image_url = ""
    status = "staged"
    timeout = 600  # 10 minutes timeout

    start_time = time.time()

    while retry_count < max_retries and status not in ["finished", "completed"] and (time.time() - start_time) < timeout:
        time.sleep(min(15 * (1.5 ** retry_count), 240))  # Exponential backoff, max 240 seconds

        fetch_payload = json.dumps({"task_id": task_id})

        fetch_response = requests.post(fetch_url, headers=headers, data=fetch_payload)
        fetch_response.raise_for_status()
        fetch_result = fetch_response.json()

        status = fetch_result.get("status")
        image_urls = fetch_result.get("image_urls", [])
        original_image_url = fetch_result.get("original_image_url", "")
        percentage = fetch_result.get("percentage", "N/A")
        
        if status == "staged":
            print(f"Attempt {retry_count + 1}: Task is staged. Waiting...")
        elif status == "processing":
            print(f"Attempt {retry_count + 1}: Processing ({percentage}% complete). Waiting...")
        elif status in ["finished", "completed"]:
            print("Image generation completed.")
            break
        else:
            print(f"Unexpected status: {status}. Stopping retries.")
            break

        retry_count += 1

    if status in ["finished", "completed"] and image_urls:
        print(f"Original Image URL: {original_image_url}")
        print("Generated Image URLs:")
        for url in image_urls:
            print(url)
        
        # Save URLs to a file
        with open('image_urls.txt', 'w') as f:
            f.write(f"Imagine Task ID: {task_id}\n")
            f.write(f"Original Image URL: {original_image_url}\n")
            f.write("Generated Image URLs:\n")
            for url in image_urls:
                f.write(f"{url}\n")
        print("Image URLs saved to image_urls.txt")
    else:
        print(f"Failed to retrieve completed image URLs. Final status: {status}")
        print(f"Final response: {json.dumps(fetch_result, indent=2)}")

except requests.exceptions.RequestException as e:
    print(f"Request error: {e}")
except ValueError as e:
    print(f"Value error: {e}")