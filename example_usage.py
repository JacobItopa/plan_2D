import requests
import time
import os
import sys

# Example Usage for Developers
# This script demonstrates how to call the endpoints of the NanoBanana Plan Scaler service.

# 1. Configuration
API_URL = "https://plan-2d.onrender.com"  # Adjust if running on a different host
IMAGE_PATH = "WhatsApp Image 2025-09-08 at 12.03.28.jpeg"     # Path to your local image file

def process_plan(image_path):
    print(f"Uploading {image_path}...")
    
    # Check if file exists
    if not os.path.exists(image_path):
        print(f"Error: File {image_path} not found.")
        # Create a dummy file if it doesn't exist for demo purposes? 
        # Better to just ask user to provide one.
        # But for this script to be runnable out of the box, we might want to skip if missing.
        return

    url = f"{API_URL}/api/process"
    files = {'file': open(image_path, 'rb')}
    
    try:
        response = requests.post(url, files=files)
        response.raise_for_status()
        data = response.json()
        
        task_id = data.get('taskId')
        print(f"Task started! ID: {task_id}")
        return task_id
        
    except requests.exceptions.HTTPError as e:
        print(f"API HTTP Error: {e.response.status_code}")
        print(f"Response Body: {e.response.text}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def wait_for_completion(task_id):
    print("Waiting for completion...")
    
    url = f"{API_URL}/api/status/{task_id}"
    
    while True:
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            success_flag = data.get('successFlag')
            
            if success_flag == 1:
                print("\nSuccess!")
                result_url = data.get('response', {}).get('resultImageUrl')
                print(f"Result Image URL: {result_url}")
                return result_url
                
            elif success_flag in [2, 3]:
                error = data.get('errorMessage', 'Unknown error')
                print(f"\nFailed: {error}")
                sys.exit(1)
                
            else:
                print(".", end="", flush=True)
                time.sleep(2)
                
        except Exception as e:
            print(f"\nError polling status: {e}")
            break

if __name__ == "__main__":
    if len(sys.argv) > 1:
        IMAGE_PATH = sys.argv[1]
    
    print("--- NanoBanana Plan Scaler Client ---")
    
    task_id = process_plan(IMAGE_PATH)
    if task_id:
        wait_for_completion(task_id)
