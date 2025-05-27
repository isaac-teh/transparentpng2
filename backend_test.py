#!/usr/bin/env python3
"""
Backend API Testing Suite for Background Removal Application
Tests the FastAPI backend endpoints for functionality, validation, and error handling.
"""

import requests
import json
import time
import base64
import os
from pathlib import Path
from PIL import Image
import io

# Get backend URL from environment
BACKEND_URL = "https://e90f7419-9a2c-4e0b-a4aa-01b1399ee4a2.preview.emergentagent.com/api"

class BackgroundRemovalAPITester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.test_results = []
        
    def log_test(self, test_name, success, message, details=None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details or {},
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name} - {message}")
        if details:
            for key, value in details.items():
                print(f"  {key}: {value}")
        print()

    def create_test_image(self, width=100, height=100, format='JPEG'):
        """Create a test image for upload testing"""
        # Create a simple test image
        img = Image.new('RGB', (width, height), color='red')
        img_buffer = io.BytesIO()
        img.save(img_buffer, format=format)
        img_buffer.seek(0)
        return img_buffer.getvalue()

    def create_large_test_image(self):
        """Create a large test image (>20MB) for size validation testing"""
        # Create a large image that will exceed 20MB when saved
        # Use larger dimensions and uncompressed format
        img = Image.new('RGB', (8000, 8000), color='blue')
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='BMP')  # BMP is uncompressed, will be larger
        img_buffer.seek(0)
        data = img_buffer.getvalue()
        
        # If still not large enough, create even larger or duplicate data
        if len(data) <= 20 * 1024 * 1024:
            # Create multiple copies to ensure we exceed 20MB
            multiplier = (20 * 1024 * 1024 // len(data)) + 2
            data = data * multiplier
        
        return data

    def test_api_health_check(self):
        """Test 1: API Health Check - GET /api/"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "Background Removal API Ready" in data["message"]:
                    self.log_test(
                        "API Health Check",
                        True,
                        "API is responding correctly",
                        {"status_code": response.status_code, "response": data}
                    )
                    return True
                else:
                    self.log_test(
                        "API Health Check",
                        False,
                        "API responded but with unexpected message",
                        {"status_code": response.status_code, "response": data}
                    )
                    return False
            else:
                self.log_test(
                    "API Health Check",
                    False,
                    f"API returned status code {response.status_code}",
                    {"status_code": response.status_code, "response": response.text}
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "API Health Check",
                False,
                f"Failed to connect to API: {str(e)}",
                {"error": str(e)}
            )
            return False

    def test_background_removal_base64(self):
        """Test 2: Background Removal API - POST /api/remove-background-base64"""
        try:
            # Create test image
            test_image = self.create_test_image()
            
            # Prepare multipart form data
            files = {'file': ('test_image.jpg', test_image, 'image/jpeg')}
            
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/remove-background-base64",
                files=files,
                timeout=30
            )
            request_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                required_fields = ['success', 'original_image', 'processed_image', 'processing_time', 'original_size', 'processed_size', 'message']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test(
                        "Background Removal Base64",
                        False,
                        f"Response missing required fields: {missing_fields}",
                        {"response": data}
                    )
                    return False
                
                # Validate base64 images
                original_valid = data['original_image'].startswith('data:image/')
                processed_valid = data['processed_image'].startswith('data:image/png;base64,')
                
                if not original_valid or not processed_valid:
                    self.log_test(
                        "Background Removal Base64",
                        False,
                        "Invalid base64 image format in response",
                        {
                            "original_valid": original_valid,
                            "processed_valid": processed_valid,
                            "original_prefix": data['original_image'][:50],
                            "processed_prefix": data['processed_image'][:50]
                        }
                    )
                    return False
                
                self.log_test(
                    "Background Removal Base64",
                    True,
                    "Background removal successful with valid response",
                    {
                        "processing_time": f"{data['processing_time']:.2f}s",
                        "original_size": f"{data['original_size']} bytes",
                        "processed_size": f"{data['processed_size']} bytes",
                        "request_time": f"{request_time:.2f}s",
                        "success": data['success']
                    }
                )
                return True
                
            else:
                self.log_test(
                    "Background Removal Base64",
                    False,
                    f"API returned status code {response.status_code}",
                    {"status_code": response.status_code, "response": response.text}
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "Background Removal Base64",
                False,
                f"Request failed: {str(e)}",
                {"error": str(e)}
            )
            return False

    def test_file_size_validation(self):
        """Test 3: File Size Validation - Test with file > 20MB"""
        try:
            # Create large test image
            large_image = self.create_large_test_image()
            
            # Check if image is actually large enough
            if len(large_image) <= 20 * 1024 * 1024:
                self.log_test(
                    "File Size Validation",
                    False,
                    "Could not create test image larger than 20MB",
                    {"actual_size": f"{len(large_image)} bytes"}
                )
                return False
            
            files = {'file': ('large_test_image.jpg', large_image, 'image/jpeg')}
            
            response = requests.post(
                f"{self.base_url}/remove-background-base64",
                files=files,
                timeout=30
            )
            
            if response.status_code == 413:
                # Expected behavior - file too large
                self.log_test(
                    "File Size Validation",
                    True,
                    "Correctly rejected file larger than 20MB",
                    {
                        "status_code": response.status_code,
                        "file_size": f"{len(large_image)} bytes",
                        "response": response.text
                    }
                )
                return True
            else:
                self.log_test(
                    "File Size Validation",
                    False,
                    f"Expected 413 status code but got {response.status_code}",
                    {
                        "status_code": response.status_code,
                        "file_size": f"{len(large_image)} bytes",
                        "response": response.text
                    }
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "File Size Validation",
                False,
                f"Request failed: {str(e)}",
                {"error": str(e)}
            )
            return False

    def test_invalid_file_type(self):
        """Test 4: Invalid File Type - Test with non-image file"""
        try:
            # Create a text file instead of image
            text_content = b"This is not an image file, it's just text content."
            
            files = {'file': ('test.txt', text_content, 'text/plain')}
            
            response = requests.post(
                f"{self.base_url}/remove-background-base64",
                files=files,
                timeout=10
            )
            
            if response.status_code == 400:
                # Expected behavior - invalid file type
                self.log_test(
                    "Invalid File Type Validation",
                    True,
                    "Correctly rejected non-image file",
                    {
                        "status_code": response.status_code,
                        "content_type": "text/plain",
                        "response": response.text
                    }
                )
                return True
            else:
                self.log_test(
                    "Invalid File Type Validation",
                    False,
                    f"Expected 400 status code but got {response.status_code}",
                    {
                        "status_code": response.status_code,
                        "content_type": "text/plain",
                        "response": response.text
                    }
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "Invalid File Type Validation",
                False,
                f"Request failed: {str(e)}",
                {"error": str(e)}
            )
            return False

    def test_background_removal_direct(self):
        """Test 5: Background Removal Direct - POST /api/remove-background (returns PNG)"""
        try:
            # Create test image
            test_image = self.create_test_image()
            
            files = {'file': ('test_image.jpg', test_image, 'image/jpeg')}
            
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/remove-background",
                files=files,
                timeout=30
            )
            request_time = time.time() - start_time
            
            if response.status_code == 200:
                # Check if response is PNG
                if response.headers.get('content-type') == 'image/png':
                    # Check for processing headers
                    processing_time = response.headers.get('X-Processing-Time')
                    original_size = response.headers.get('X-Original-Size')
                    processed_size = response.headers.get('X-Processed-Size')
                    
                    self.log_test(
                        "Background Removal Direct",
                        True,
                        "Background removal successful, returned PNG image",
                        {
                            "content_type": response.headers.get('content-type'),
                            "content_length": len(response.content),
                            "processing_time": processing_time,
                            "original_size": original_size,
                            "processed_size": processed_size,
                            "request_time": f"{request_time:.2f}s"
                        }
                    )
                    return True
                else:
                    self.log_test(
                        "Background Removal Direct",
                        False,
                        f"Expected PNG image but got {response.headers.get('content-type')}",
                        {"content_type": response.headers.get('content-type')}
                    )
                    return False
            else:
                self.log_test(
                    "Background Removal Direct",
                    False,
                    f"API returned status code {response.status_code}",
                    {"status_code": response.status_code, "response": response.text}
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "Background Removal Direct",
                False,
                f"Request failed: {str(e)}",
                {"error": str(e)}
            )
            return False

    def test_png_image_upload(self):
        """Test 6: PNG Image Upload - Test with PNG format"""
        try:
            # Create PNG test image
            test_image = self.create_test_image(format='PNG')
            
            files = {'file': ('test_image.png', test_image, 'image/png')}
            
            response = requests.post(
                f"{self.base_url}/remove-background-base64",
                files=files,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success') and 'processed_image' in data:
                    self.log_test(
                        "PNG Image Upload",
                        True,
                        "PNG image processed successfully",
                        {
                            "processing_time": f"{data['processing_time']:.2f}s",
                            "original_size": f"{data['original_size']} bytes",
                            "processed_size": f"{data['processed_size']} bytes"
                        }
                    )
                    return True
                else:
                    self.log_test(
                        "PNG Image Upload",
                        False,
                        "PNG processing failed or incomplete response",
                        {"response": data}
                    )
                    return False
            else:
                self.log_test(
                    "PNG Image Upload",
                    False,
                    f"PNG upload failed with status {response.status_code}",
                    {"status_code": response.status_code, "response": response.text}
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "PNG Image Upload",
                False,
                f"Request failed: {str(e)}",
                {"error": str(e)}
            )
            return False

    def run_all_tests(self):
        """Run all backend tests"""
        print("=" * 80)
        print("BACKGROUND REMOVAL BACKEND API TESTING")
        print("=" * 80)
        print(f"Testing backend at: {self.base_url}")
        print()
        
        # Run tests in order of priority
        tests = [
            self.test_api_health_check,
            self.test_background_removal_base64,
            self.test_background_removal_direct,
            self.test_png_image_upload,
            self.test_file_size_validation,
            self.test_invalid_file_type,
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed += 1
            except Exception as e:
                self.log_test(
                    test.__name__,
                    False,
                    f"Test crashed with exception: {str(e)}",
                    {"exception": str(e)}
                )
        
        print("=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print(f"Tests passed: {passed}/{total}")
        print(f"Success rate: {(passed/total)*100:.1f}%")
        print()
        
        # Print detailed results
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}: {result['message']}")
        
        return passed, total, self.test_results

def main():
    """Main testing function"""
    tester = BackgroundRemovalAPITester(BACKEND_URL)
    passed, total, results = tester.run_all_tests()
    
    # Save results to file
    with open('/app/backend_test_results.json', 'w') as f:
        json.dump({
            'summary': {
                'passed': passed,
                'total': total,
                'success_rate': (passed/total)*100
            },
            'results': results
        }, f, indent=2)
    
    print(f"\nDetailed results saved to: /app/backend_test_results.json")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)