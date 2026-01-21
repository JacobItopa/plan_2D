import httpx
import time
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

class NanoBananaAPI:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("NANOBANANA_API_KEY")
        if not self.api_key:
            # Print to logs for debugging on Render
            print("CRITICAL: NANOBANANA_API_KEY is missing!")
        
        self.base_url = 'https://api.nanobananaapi.ai/api/v1/nanobanana'
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    async def generate_image(self, prompt, **options):
        data = {
            'prompt': prompt,
            'type': options.get('type', 'TEXTTOIAMGE'),
            'numImages': options.get('numImages', 1),
            'callBackUrl': options.get('callBackUrl'),
            'watermark': options.get('watermark')
        }
        
        if options.get('imageUrls'):
            data['imageUrls'] = options['imageUrls']
        
        timeout = httpx.Timeout(30.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                print(f"DEBUG: Calling NanoBanana Generation Endpoint: {self.base_url}/generate with data={data}")
                response = await client.post(f'{self.base_url}/generate', 
                                           headers=self.headers, json=data)
                
                # Check for HTTP errors
                if response.status_code >= 400:
                    print(f"ERROR: NanoBanana API returned {response.status_code}: {response.text}")
                    # Try to parse error message if possible
                    try:
                        err_json = response.json()
                        error_detail = err_json.get('msg', response.text)
                    except:
                        error_detail = response.text
                    raise Exception(f"API Error ({response.status_code}): {error_detail}")

                result = response.json()
                
                if result.get('code') != 200:
                    msg = result.get('msg', 'Unknown error')
                    print(f"ERROR: NanoBanana Business Logic Error: {msg}")
                    raise Exception(f"Generation failed: {msg}")
                
                return result['data']['taskId']
            except httpx.RequestError as exc:
                 print(f"ERROR: An error occurred while requesting {exc.request.url!r}.")
                 raise Exception(f"Connection error to NanoBanana: {exc}")

    async def get_task_status(self, task_id):
        async with httpx.AsyncClient() as client:
            response = await client.get(f'{self.base_url}/record-info?taskId={task_id}',
                                      headers={'Authorization': f'Bearer {self.api_key}'})
            if response.status_code != 200:
                 print(f"ERROR checking status: {response.text}")
                 raise Exception(f"Status check failed: {response.text}")
            return response.json()
