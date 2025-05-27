#!/usr/bin/env python3
"""
Script to pre-download the rembg AI model during Docker build
"""

import rembg
from rembg import remove
from PIL import Image
import io

def download_model():
    print('Pre-downloading AI model...')
    
    # Create a small dummy image to trigger model download
    dummy_image = Image.new('RGB', (100, 100), color='red')
    img_byte_arr = io.BytesIO()
    dummy_image.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    
    # This will trigger the model download
    try:
        result = remove(img_byte_arr)
        print(f'Model downloaded successfully! Result size: {len(result)} bytes')
    except Exception as e:
        print(f'Model download completed with: {e}')

if __name__ == '__main__':
    download_model() 