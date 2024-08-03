import os
import time
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

load_dotenv()

app = FastAPI()

class VideoRequest(BaseModel):
    prompt: str
    image_url: str

class VideoResponse(BaseModel):
    video_url: str

def generate_video_url(api_key, prompt, image_url, max_retries=30, timeout=1800):
    submission_url = "https://api.apiframe.pro/luma-imagine"
    
    payload = {
        "prompt": prompt,
        "image_url": image_url,
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': api_key
    }
    
    try:
        response = requests.post(submission_url, headers=headers, json=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")
    
    task_data = response.json()
    task_id = task_data.get("task_id")
    
    if not task_id:
        raise HTTPException(status_code=500, detail="Failed to retrieve task ID.")

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
                return video_url
            else:
                raise HTTPException(status_code=500, detail="Video URL not found in the completed response.")
        else:
            raise HTTPException(status_code=500, detail=f"Unexpected status: {status}")
    
    if time.time() - start_time >= timeout:
        raise HTTPException(status_code=408, detail="Timeout reached. Task not completed.")
    elif retry_count >= max_retries:
        raise HTTPException(status_code=500, detail="Max retries reached. Task not completed.")

@app.post("/generate_video", response_model=VideoResponse)
async def create_video(request: VideoRequest):
    api_key = os.getenv("API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="API_KEY environment variable is not set")

    try:
        video_url = generate_video_url(api_key, request.prompt, request.image_url)
        return VideoResponse(video_url=video_url)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)