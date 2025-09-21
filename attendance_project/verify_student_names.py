#!/usr/bin/env python3
"""
Script to verify student names are properly loaded
"""

import requests
import json

def verify_student_names():
    """Check the current student names in the system"""
    
    try:
        # Get students from API
        response = requests.get('http://localhost:5000/api/students')
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                students = data.get('students', [])
                
                print(f"✅ Successfully loaded {len(students)} students with proper names:")
                print("=" * 60)
                
                for student in sorted(students, key=lambda x: x['student_name']):
                    print(f"ID: {student['student_id']:<20} Name: {student['student_name']}")
                
                print("=" * 60)
                print(f"Total: {len(students)} students")
                
                # Check for any remaining generic names
                generic_names = [s for s in students if s['student_name'].startswith('Student ')]
                if generic_names:
                    print(f"⚠️  Found {len(generic_names)} students with generic names:")
                    for student in generic_names:
                        print(f"  - {student['student_id']}: {student['student_name']}")
                else:
                    print("✅ All students have proper names!")
                
            else:
                print(f"❌ API Error: {data.get('message', 'Unknown error')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        print("Make sure the Flask server is running on http://localhost:5000")

if __name__ == "__main__":
    verify_student_names()
