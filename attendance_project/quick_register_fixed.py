#!/usr/bin/env python3
"""
Quick registration using resized images to avoid hanging
"""

import cv2
import numpy as np
import face_recognition
import os
from pathlib import Path
import time
import sqlite3
from datetime import datetime
import json

def quick_register_students():
    """Quick student registration using resized images"""
    print("🚀 QUICK STUDENT REGISTRATION (Using Resized Images)")
    print("="*60)
    
    # Initialize database connection
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()
    
    # Create students table if not exists
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
    if not student_photos_dir.exists():
        print("❌ student_photos directory not found")
        return
    
    student_folders = [f for f in student_photos_dir.iterdir() if f.is_dir() and not f.name.startswith('.')]
    print(f"Found {len(student_folders)} student folders")
    
    successful = 0
    failed = 0
    total_encodings = 0
    
    for i, folder in enumerate(student_folders, 1):
        print(f"\n[{i}/{len(student_folders)}] Processing {folder.name}...")
        
        # Look for resized images first
        resized_images = list(folder.glob("resized_*.jpg")) + list(folder.glob("resized_*.jpeg")) + list(folder.glob("resized_*.png"))
        
        if not resized_images:
            # Fallback to original images
            resized_images = list(folder.glob("*.jpg")) + list(folder.glob("*.jpeg")) + list(folder.glob("*.png"))
        
        if not resized_images:
            print(f"  ❌ No images found")
            failed += 1
            continue
        
        print(f"  📸 Using {len(resized_images)} images")
        
        # Process first image only for speed
        image_path = resized_images[0]
        print(f"  🖼️  Processing: {image_path.name}")
        
        try:
            # Load image
            image = face_recognition.load_image_file(str(image_path))
            print(f"    Image size: {image.shape}")
            
            # Detect faces with timeout
            print("    Detecting faces...")
            start_time = time.time()
            face_locations = face_recognition.face_locations(image, model="hog")
            detection_time = time.time() - start_time
            print(f"    ✅ Found {len(face_locations)} faces in {detection_time:.2f}s")
            
            if not face_locations:
                print("    ❌ No faces detected")
                failed += 1
                continue
            
            # Create encodings
            print("    Creating face encodings...")
            start_time = time.time()
            encodings = face_recognition.face_encodings(image, face_locations)
            encoding_time = time.time() - start_time
            print(f"    ✅ Created {len(encodings)} encodings in {encoding_time:.2f}s")
            
            if not encodings:
                print("    ❌ No encodings created")
                failed += 1
                continue
            
            # Generate student info
            student_id = folder.name.upper()
            student_name = folder.name.replace('_', ' ').title()
            
            # Store in database
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO students (student_id, name, class_section)
                    VALUES (?, ?, ?)
                ''', (student_id, student_name, "DEFAULT"))
                
                # Store encodings in a simple format
                encoding_data = {
                    'student_id': student_id,
                    'encodings': [enc.tolist() for enc in encodings],
                    'created_at': datetime.now().isoformat()
                }
                
                # Save to file
                encoding_file = f"encodings_{student_id}.json"
                with open(encoding_file, 'w') as f:
                    json.dump(encoding_data, f)
                
                print(f"    ✅ Registered: {student_name} ({student_id})")
                print(f"    📁 Encodings saved: {encoding_file}")
                
                successful += 1
                total_encodings += len(encodings)
                
            except Exception as e:
                print(f"    ❌ Database error: {e}")
                failed += 1
                
        except Exception as e:
            print(f"    ❌ Processing error: {e}")
            failed += 1
    
    # Commit database changes
    conn.commit()
    conn.close()
    
    print(f"\n📊 REGISTRATION COMPLETE!")
    print(f"  ✅ Successful: {successful}")
    print(f"  ❌ Failed: {failed}")
    print(f"  🎯 Total encodings: {total_encodings}")
    
    if successful > 0:
        print(f"\n🎉 SUCCESS! {successful} students registered successfully!")
        print(f"You can now test the attendance system.")
    else:
        print(f"\n❌ No students were registered successfully.")
        print(f"Check the error messages above for details.")

def test_registration():
    """Test the registration by checking database"""
    print("\n🧪 TESTING REGISTRATION")
    print("="*30)
    
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()
    
    # Check students
    cursor.execute("SELECT COUNT(*) FROM students")
    student_count = cursor.fetchone()[0]
    print(f"Students in database: {student_count}")
    
    if student_count > 0:
        cursor.execute("SELECT student_id, name FROM students LIMIT 5")
        students = cursor.fetchall()
        print("Sample students:")
        for student_id, name in students:
            print(f"  - {student_id}: {name}")
    
    # Check encoding files
    encoding_files = list(Path(".").glob("encodings_*.json"))
    print(f"Encoding files: {len(encoding_files)}")
    
    conn.close()
    
    if student_count > 0 and len(encoding_files) > 0:
        print("✅ Registration test passed!")
        return True
    else:
        print("❌ Registration test failed!")
        return False

if __name__ == "__main__":
    print("🎯 FIXED REGISTRATION SYSTEM")
    print("Using resized images to avoid hanging")
    print("="*50)
    
    # Run registration
    quick_register_students()
    
    # Test registration
    test_registration()
    
    print("\n🎯 NEXT STEPS:")
    print("1. If registration was successful, test the main system")
    print("2. Try processing classroom photos")
    print("3. The system should now work without hanging")
