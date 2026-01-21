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
        img_url = data.get('originalImageUrl', 'N/A')
        
        print(f"Task started! ID: {task_id}")
        print(f"Uploaded Image URL (sent to API): {img_url}")
        return task_id
        
    except requests.exceptions.HTTPError as e:
        print(f"API HTTP Error: {e.response.status_code}")
        print(f"Response Body: {e.response.text}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def download_image(url, output_path):
    print(f"Downloading result to {output_path}...")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print("Download complete!")
    except Exception as e:
        print(f"Failed to download image: {e}")

def wait_for_completion(task_id):
    print("Waiting for completion...")
    
    url = f"{API_URL}/api/status/{task_id}"
    consecutive_errors = 0
    
    while True:
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            # DEBUG: Print the full structure to see where 'successFlag' is hiding
            print(f"\nDEBUG Status Response: {data}")
            
            # Reset error count on success
            consecutive_errors = 0
            
            # Attempt to find successFlag. 
            # If it's wrapped in 'data', we might need to look there.
            if 'data' in data and isinstance(data['data'], dict):
                 success_flag = data['data'].get('successFlag')
                 # Update data pointer if needed, or just extract what we need
                 payload = data['data']
            else:
                 success_flag = data.get('successFlag')
                 payload = data # Fallback
            
            if success_flag == 1:
                print("\nSuccess! JSON Response:")
                print(data) # Print full JSON response
                result_url = payload.get('response', {}).get('resultImageUrl')
                print(f"Result Image URL: {result_url}")
                return result_url
            
            elif success_flag in [2, 3]:
                error = payload.get('errorMessage', 'Unknown error')
                print(f"\nFailed: {error}")
                print(f"Full Response: {data}")
                sys.exit(1)
                
            else:
                # Debugging: Print status
                print(f"Status: {success_flag} (Generating...)")
                # print(".", end="", flush=True)
                time.sleep(3)
                
        except (requests.exceptions.ConnectionError, requests.exceptions.ChunkedEncodingError) as e:
            consecutive_errors += 1
            print(f"!", end="", flush=True) # Indicate error
            if consecutive_errors > 5:
                print(f"\nToo many connection errors: {e}")
                break
            time.sleep(2)
            
        except requests.exceptions.HTTPError as e:
            print(f"\nAPI HTTP Error: {e.response.status_code}")
            print(f"Response Body: {e.response.text}")
            sys.exit(1)
            
        except Exception as e:
            print(f"\nError polling status: {e}")
            break

if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1]
    else:
        arg = IMAGE_PATH # Default
    
    print("--- NanoBanana Plan Scaler Client ---")
    
    task_id = None
    
    # Check if argument is a file or a Task ID
    if os.path.exists(arg):
        task_id = process_plan(arg)
    else:
        # Assume it's a Task ID if acceptable length/format, or just try it.
        print(f"Argument '{arg}' is not a file. Assuming it is a Task ID.")
        task_id = arg
    
    if task_id:
        result_url = wait_for_completion(task_id)
        if result_url:
            # If we started with a file, we can name it nicely. 
            # If we started with a task ID, we use a generic name.
            if os.path.exists(arg):
                output_filename = f"processed_{os.path.basename(arg)}"
            else:
                output_filename = f"processed_task_{task_id}.png" # Default ext
                
            download_image(result_url, output_filename)
