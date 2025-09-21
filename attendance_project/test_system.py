#!/usr/bin/env python3
"""
Test script for Smart Attendance System
Tests the complete system functionality including API endpoints
"""

import requests
import json
import os
import time
import base64
from datetime import datetime
from smart_attendance_system import OptimizedAttendanceSystem

class AttendanceSystemTester:
    def __init__(self):
        self.base_url = "http://localhost:5000/api"
        self.system = OptimizedAttendanceSystem()
        self.test_results = []
        
    def log_test(self, test_name, success, message=""):
        """Log test results"""
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"   {message}")
        
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
    
    def test_backend_system(self):
        """Test the backend attendance system"""
        print("\n=== Testing Backend System ===")
        
        try:
            # Test system initialization
            self.system.verify_system_setup()
            self.log_test("Backend System Initialization", True, "System initialized successfully")
        except Exception as e:
            self.log_test("Backend System Initialization", False, str(e))
            return False
        
        # Test directory structure
        required_dirs = [
            self.system.student_data_path,
            self.system.attendance_path,
            self.system.models_path,
            self.system.logs_path,
            self.system.batch_images_path,
            self.system.classroom_images_path
        ]
        
        all_dirs_exist = True
        for dir_path in required_dirs:
            if not os.path.exists(dir_path):
                all_dirs_exist = False
                break
        
        self.log_test("Directory Structure", all_dirs_exist, 
                     f"Required directories {'exist' if all_dirs_exist else 'missing'}")
        
        # Test student database
        student_count = len(self.system.student_database)
        self.log_test("Student Database", student_count > 0, 
                     f"Found {student_count} registered students")
        
        return True
    
    def test_api_endpoints(self):
        """Test Flask API endpoints"""
        print("\n=== Testing API Endpoints ===")
        
        # Test health endpoint
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.log_test("Health Endpoint", True, 
                             f"Status: {data.get('status', 'unknown')}")
            else:
                self.log_test("Health Endpoint", False, 
                             f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Health Endpoint", False, str(e))
            return False
        
        # Test students endpoint
        try:
            response = requests.get(f"{self.base_url}/students", timeout=10)
            if response.status_code == 200:
                data = response.json()
                student_count = data.get('total_count', 0)
                self.log_test("Students Endpoint", True, 
                             f"Retrieved {student_count} students")
            else:
                self.log_test("Students Endpoint", False, 
                             f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Students Endpoint", False, str(e))
        
        # Test attendance history endpoint
        try:
            response = requests.get(f"{self.base_url}/attendance-history", timeout=10)
            if response.status_code == 200:
                data = response.json()
                history_count = len(data.get('history', []))
                self.log_test("History Endpoint", True, 
                             f"Retrieved {history_count} history records")
            else:
                self.log_test("History Endpoint", False, 
                             f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("History Endpoint", False, str(e))
        
        return True
    
    def test_image_processing(self):
        """Test image processing functionality"""
        print("\n=== Testing Image Processing ===")
        
        # Look for test images in classroom_photos
        test_images = []
        if os.path.exists(self.system.classroom_images_path):
            for file in os.listdir(self.system.classroom_images_path):
                if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                    test_images.append(os.path.join(self.system.classroom_images_path, file))
        
        if not test_images:
            self.log_test("Image Processing", False, 
                         "No test images found in classroom_photos directory")
            return False
        
        # Test with first available image
        test_image = test_images[0]
        try:
            # Test image upload via API
            with open(test_image, 'rb') as f:
                files = {'file': f}
                response = requests.post(f"{self.base_url}/upload-image", 
                                       files=files, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    faces_detected = data.get('total_faces', 0)
                    recognized = data.get('recognized_count', 0)
                    self.log_test("Image Processing", True, 
                                 f"Detected {faces_detected} faces, recognized {recognized}")
                else:
                    self.log_test("Image Processing", False, 
                                 data.get('message', 'Unknown error'))
            else:
                self.log_test("Image Processing", False, 
                             f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Image Processing", False, str(e))
        
        return True
    
    def test_csv_generation(self):
        """Test CSV file generation and download"""
        print("\n=== Testing CSV Generation ===")
        
        # Check for existing CSV files
        csv_files = []
        if os.path.exists(self.system.attendance_path):
            for file in os.listdir(self.system.attendance_path):
                if file.endswith('.csv') and file.startswith('attendance_'):
                    csv_files.append(file)
        
        if csv_files:
            # Test downloading an existing CSV
            test_csv = csv_files[0]
            try:
                response = requests.get(f"{self.base_url}/download-csv/{test_csv}", 
                                      timeout=10)
                if response.status_code == 200:
                    self.log_test("CSV Download", True, 
                                 f"Successfully downloaded {test_csv}")
                else:
                    self.log_test("CSV Download", False, 
                                 f"HTTP {response.status_code}")
            except Exception as e:
                self.log_test("CSV Download", False, str(e))
        else:
            self.log_test("CSV Generation", False, 
                         "No CSV files found - process an image first")
        
        return True
    
    def run_all_tests(self):
        """Run all system tests"""
        print("Smart Attendance System - Comprehensive Test Suite")
        print("=" * 60)
        
        start_time = time.time()
        
        # Run tests
        self.test_backend_system()
        self.test_api_endpoints()
        self.test_image_processing()
        self.test_csv_generation()
        
        # Generate summary
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n=== Test Summary ===")
        print(f"Total tests run: {len(self.test_results)}")
        print(f"Passed: {sum(1 for r in self.test_results if r['success'])}")
        print(f"Failed: {sum(1 for r in self.test_results if not r['success'])}")
        print(f"Duration: {duration:.2f} seconds")
        
        # Save detailed results
        results_file = os.path.join(self.system.logs_path, 
                                   f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        try:
            with open(results_file, 'w') as f:
                json.dump({
                    'summary': {
                        'total_tests': len(self.test_results),
                        'passed': sum(1 for r in self.test_results if r['success']),
                        'failed': sum(1 for r in self.test_results if not r['success']),
                        'duration': duration,
                        'timestamp': datetime.now().isoformat()
                    },
                    'results': self.test_results
                }, f, indent=2)
            print(f"\nDetailed results saved to: {results_file}")
        except Exception as e:
            print(f"Failed to save results: {e}")
        
        # Return overall success
        return all(r['success'] for r in self.test_results)

def main():
    """Main test function"""
    print("Starting Smart Attendance System Tests...")
    print("Make sure the Flask API server is running on http://localhost:5000")
    print()
    
    # Wait a moment for user to read
    time.sleep(2)
    
    tester = AttendanceSystemTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All tests passed! System is ready for use.")
    else:
        print("\n⚠️  Some tests failed. Please check the issues above.")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
