import requests
import json
import time
import os
from dotenv import load_dotenv

load_dotenv()

# Define the function to generate a video URL from a prompt and image URL
import requests
import json
import time
import os

def generate_video_url(api_key, prompt, image_url, enhance_prompt=False, max_retries=30, timeout=1800):
    submission_url = "https://api.apiframe.pro/luma-imagine"
    
    payload = {
        "prompt": prompt,
        "image_url": image_url,
        "enhance_prompt": enhance_prompt
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': api_key
    }
    
    try:
        response = requests.post(submission_url, headers=headers, json=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}", "details": response.text if response else None}
    
    task_data = response.json()
    task_id = task_data.get("task_id")
    
    if not task_id:
        return {"error": "Failed to retrieve task ID.", "details": task_data}

    fetch_url = "https://api.apiframe.pro/fetch"
    
    retry_count = 0
    start_time = time.time()
    status = "staged"

    while retry_count < max_retries and status not in ["completed", "finished", "success"] and (time.time() - start_time) < timeout:
        fetch_payload = {"task_id": task_id}
        
        try:
            fetch_response = requests.post(fetch_url, headers=headers, json=fetch_payload)
            fetch_response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch task result: {str(e)}. Retrying...")
            retry_count += 1
            time.sleep(min(10 * (1.2 ** retry_count), 60))
            continue
        
        result = fetch_response.json()
        print(result)  # Debugging: Log the result
        
        status = result.get("status")
        if status in ["staged", "processing"]:
            print(f"Status: {status}, Progress: {result.get('percentage', 'unknown')}%")
            retry_count += 1
            time.sleep(min(10 * (1.2 ** retry_count), 60))  # Exponential backoff, max 60 seconds
        elif status in ["completed", "finished", "success"]:
            video_url = result.get("video_url")
            if video_url:
                return {"video_url": video_url}
            else:
                return {"error": "Video URL not found in the completed response.", "details": result}
        else:
            return {"error": f"Unexpected status: {status}", "details": result}
    
    if time.time() - start_time >= timeout:
        return {"error": "Timeout reached. Task not completed.", "details": result}
    elif retry_count >= max_retries:
        return {"error": "Max retries reached. Task not completed.", "details": result}



# Make sure to set this environment variable before running the script
api_key = os.getenv("API_KEY")
if not api_key:
    raise ValueError("API_KEY environment variable is not set")

prompt = "Explosion"
image_url = "https://yudhisteer.github.io/Git/cat.png"

video_result = generate_video_url(api_key, prompt, image_url)
print(video_result)