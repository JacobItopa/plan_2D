import requests
import time
import os
from dotenv import load_dotenv

load_dotenv()

class NanoBananaAPI:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("NANOBANANA_API_KEY")
        if not self.api_key:
            raise ValueError("NanoBanana API Key is required")
        self.base_url = 'https://api.nanobananaapi.ai/api/v1/nanobanana'
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def generate_image(self, prompt, **options):
        data = {
            'prompt': prompt,
            'type': options.get('type', 'TEXTTOIAMGE'),
            'numImages': options.get('numImages', 1),
            'callBackUrl': options.get('callBackUrl'),
            'watermark': options.get('watermark')
        }
        
        if options.get('imageUrls'):
            data['imageUrls'] = options['imageUrls'] # Expects a list of strings
        
        # print(f"DEBUG: Sending request to {self.base_url}/generate with data: {data}")
        response = requests.post(f'{self.base_url}/generate', 
                               headers=self.headers, json=data)
        result = response.json()
        
        if not response.ok or result.get('code') != 200:
            raise Exception(f"Generation failed: {result.get('msg', 'Unknown error')}")
        
        return result['data']['taskId']
    
    def get_task_status(self, task_id):
        response = requests.get(f'{self.base_url}/record-info?taskId={task_id}',
                              headers={'Authorization': f'Bearer {self.api_key}'})
        return response.json()
    
    def wait_for_completion(self, task_id, max_wait_time=300):
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            status = self.get_task_status(task_id)
            success_flag = status.get('successFlag', 0)
            
            if success_flag == 1:
                return status.get('response', {})
            elif success_flag in [2, 3]:
                error_msg = status.get('errorMessage', 'Generation failed')
                raise Exception(error_msg)
            
            time.sleep(3)
        
        raise Exception('Generation timeout')
