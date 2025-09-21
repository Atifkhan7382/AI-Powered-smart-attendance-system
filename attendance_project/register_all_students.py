#!/usr/bin/env python3
"""
Register all students using resized images
"""

import cv2
import face_recognition
import sqlite3
import json
import os
from pathlib import Path
import time
from datetime import datetime

def register_all_students():
    """Register all students using resized images"""
    print("🚀 REGISTERING ALL STUDENTS")
    print("="*40)
    
    # Initialize database
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()
    
    # Create students table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            student_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT,
            class_section TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    student_photos_dir = Path("student_photos")
    folders = [f for f in student_photos_dir.iterdir() if f.is_dir() and not f.name.startswith('.')]
    
    print(f"Found {len(folders)} student folders")
    
    successful = 0
    failed = 0
    all_encodings = {}
    
    for i, folder in enumerate(folders, 1):
        print(f"\n[{i}/{len(folders)}] Processing {folder.name}...")
        
        # Look for resized images
        resized_images = list(folder.glob("resized_*.jpg")) + list(folder.glob("resized_*.jpeg")) + list(folder.glob("resized_*.png"))
        
        if not resized_images:
            print(f"  ❌ No resized images found")
            failed += 1
            continue
        
        # Use first resized image
        image_path = resized_images[0]
        print(f"  📸 Using: {image_path.name}")
        
        try:
            # Load and process image
            image = face_recognition.load_image_file(str(image_path))
            print(f"    Size: {image.shape}")
            
            # Detect faces
            face_locations = face_recognition.face_locations(image, model="hog")
            print(f"    Faces: {len(face_locations)}")
            
            if not face_locations:
                print(f"    ❌ No faces detected")
                failed += 1
                continue
            
            # Create encodings
            encodings = face_recognition.face_encodings(image, face_locations)
            print(f"    Encodings: {len(encodings)}")
            
            if not encodings:
                print(f"    ❌ No encodings created")
                failed += 1
                continue
            
            # Generate student info
            student_id = folder.name.upper()
            student_name = folder.name.replace('_', ' ').title()
            
            # Store in database
            cursor.execute('''
                INSERT OR REPLACE INTO students (student_id, name, class_section)
                VALUES (?, ?, ?)
            ''', (student_id, student_name, "DEFAULT"))
            
            # Store encodings
            all_encodings[student_id] = {
                'name': student_name,
                'encodings': [enc.tolist() for enc in encodings],
                'created_at': datetime.now().isoformat()
            }
            
            print(f"    ✅ Registered: {student_name}")
            successful += 1
            
        except Exception as e:
            print(f"    ❌ Error: {e}")
            failed += 1
    
    # Save all encodings to file
    with open("all_student_encodings.json", "w") as f:
        json.dump(all_encodings, f, indent=2)
    
    # Commit database changes
    conn.commit()
    conn.close()
    
    print(f"\n📊 REGISTRATION COMPLETE!")
    print(f"  ✅ Successful: {successful}")
    print(f"  ❌ Failed: {failed}")
    print(f"  📁 Encodings saved: all_student_encodings.json")
    
    return successful > 0

def test_attendance_system():
    """Test the attendance system with registered students"""
    print(f"\n🧪 TESTING ATTENDANCE SYSTEM")
    print("="*40)
    
    # Load encodings
    if not os.path.exists("all_student_encodings.json"):
        print("❌ No encodings file found")
        return False
    
    with open("all_student_encodings.json", "r") as f:
        encodings_data = json.load(f)
    
    print(f"Loaded encodings for {len(encodings_data)} students")
    
    # Test with classroom photo
    classroom_photos = list(Path("classroom_photos").glob("*.jpg"))
    if not classroom_photos:
        print("❌ No classroom photos found")
        return False
    
    classroom_photo = classroom_photos[0]
    print(f"Testing with: {classroom_photo.name}")
    
    try:
        # Load classroom image
        classroom_image = face_recognition.load_image_file(str(classroom_photo))
        print(f"Classroom image size: {classroom_image.shape}")
        
        # Detect faces
        face_locations = face_recognition.face_locations(classroom_image, model="hog")
        print(f"Faces detected: {len(face_locations)}")
        
        if face_locations:
            # Create encodings for classroom faces
            classroom_encodings = face_recognition.face_encodings(classroom_image, face_locations)
            print(f"Classroom encodings: {len(classroom_encodings)}")
            
            # Try to match with registered students
            matches = 0
            for classroom_encoding in classroom_encodings:
                for student_id, student_data in encodings_data.items():
                    student_encodings = [np.array(enc) for enc in student_data['encodings']]
                    face_distances = face_recognition.face_distance(student_encodings, classroom_encoding)
                    
                    if len(face_distances) > 0 and min(face_distances) < 0.6:
                        matches += 1
                        print(f"  ✅ Match found: {student_data['name']} (distance: {min(face_distances):.3f})")
                        break
            
            print(f"Total matches: {matches}")
            return matches > 0
        else:
            print("No faces detected in classroom photo")
            return False
            
    except Exception as e:
        print(f"Error testing attendance: {e}")
        return False

if __name__ == "__main__":
    print("🎯 STUDENT REGISTRATION & TESTING")
    print("="*50)
    
    # Register students
    success = register_all_students()
    
    if success:
        print(f"\n✅ Registration successful!")
        
        # Test attendance system
        test_success = test_attendance_system()
        
        if test_success:
            print(f"\n🎉 SUCCESS! Attendance system is working!")
        else:
            print(f"\n⚠️  Registration worked but attendance testing needs improvement")
    else:
        print(f"\n❌ Registration failed!")
    
    print(f"\n🎯 NEXT STEPS:")
    print(f"1. Check the database for registered students")
    print(f"2. Try processing classroom photos")
    print(f"3. The system should now work without hanging")
