#!/usr/bin/env python3
"""
Quick Accuracy Check for Smart Attendance System
"""

import cv2
import numpy as np
import os
import time
from pathlib import Path

def check_system_status():
    """Quick system status check"""
    print("🔍 QUICK ACCURACY CHECK")
    print("="*40)
    
    # Check if face_recognition is available
    try:
        import face_recognition
        print("✅ face_recognition: Available")
        fr_available = True
    except ImportError:
        print("❌ face_recognition: Not available")
        fr_available = False
    
    # Check OpenCV
    print(f"✅ OpenCV: Version {cv2.__version__}")
    
    # Check classroom photos
    classroom_dir = Path("classroom_photos")
    if classroom_dir.exists():
        photos = list(classroom_dir.glob("*.jpg")) + list(classroom_dir.glob("*.jpeg")) + list(classroom_dir.glob("*.png"))
        print(f"✅ Classroom photos: {len(photos)} found")
        for photo in photos:
            print(f"   - {photo.name}")
    else:
        print("❌ Classroom photos: No directory found")
        photos = []
    
    # Check student database
    student_dir = Path("student_database")
    if student_dir.exists():
        students = [d for d in student_dir.iterdir() if d.is_dir()]
        print(f"✅ Student database: {len(students)} students")
        for student in students:
            images = list(student.glob("*.jpg")) + list(student.glob("*.jpeg")) + list(student.glob("*.png"))
            print(f"   - {student.name}: {len(images)} photos")
    else:
        print("❌ Student database: No directory found")
        students = []
    
    # Check database file
    if os.path.exists("attendance.db"):
        print("✅ Database: attendance.db exists")
    else:
        print("❌ Database: attendance.db not found")
    
    return fr_available, photos, students

def test_face_detection_on_photos(photos):
    """Test face detection on available photos"""
    print(f"\n📸 TESTING FACE DETECTION")
    print("="*40)
    
    if not photos:
        print("❌ No photos to test")
        return
    
    # Initialize OpenCV face detector
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    total_faces = 0
    total_time = 0
    
    for photo in photos:
        print(f"\nTesting: {photo.name}")
        
        # Load image
        image = cv2.imread(str(photo))
        if image is None:
            print(f"   ❌ Could not load image")
            continue
        
        print(f"   📏 Size: {image.shape[1]}x{image.shape[0]}")
        
        # Convert to grayscale for OpenCV detection
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        start_time = time.time()
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        detection_time = time.time() - start_time
        
        print(f"   🎯 Faces found: {len(faces)}")
        print(f"   ⏱️  Time: {detection_time:.2f}s")
        
        total_faces += len(faces)
        total_time += detection_time
        
        # Show face locations
        for i, (x, y, w, h) in enumerate(faces):
            print(f"      Face {i+1}: ({x}, {y}, {w}, {h})")
    
    # Summary
    if len(photos) > 0:
        avg_faces = total_faces / len(photos)
        avg_time = total_time / len(photos)
        
        print(f"\n📊 SUMMARY:")
        print(f"   Photos tested: {len(photos)}")
        print(f"   Total faces: {total_faces}")
        print(f"   Average faces per photo: {avg_faces:.1f}")
        print(f"   Average detection time: {avg_time:.2f}s")
        
        # Rating
        if avg_faces >= 2:
            rating = "🎯 Excellent"
        elif avg_faces >= 1:
            rating = "✅ Good"
        elif avg_faces >= 0.5:
            rating = "⚠️  Average"
        else:
            rating = "❌ Poor"
        
        print(f"   Detection rating: {rating}")

def test_with_smart_system(photos):
    """Test using the Smart Attendance System"""
    print(f"\n🤖 TESTING WITH SMART SYSTEM")
    print("="*40)
    
    try:
        from smart_attendance_system import SmartAttendanceSystem
        
        # Initialize system
        print("Initializing Smart Attendance System...")
        system = SmartAttendanceSystem()
        print("✅ System initialized")
        
        # Test on photos
        for photo in photos:
            print(f"\nTesting: {photo.name}")
            
            start_time = time.time()
            results = system.process_classroom_image(str(photo), save_annotated=False)
            processing_time = time.time() - start_time
            
            print(f"   🎯 Faces detected: {results['total_faces_detected']}")
            print(f"   👥 Students recognized: {len(results['present_students'])}")
            print(f"   ❓ Unknown faces: {results['unknown_faces']}")
            print(f"   ⏱️  Processing time: {processing_time:.2f}s")
            
            # Show recognition details
            for student in results['present_students']:
                print(f"      ✅ {student['student_id']} (confidence: {student['confidence']:.2f})")
    
    except Exception as e:
        print(f"❌ Error testing with Smart System: {e}")

def main():
    """Run quick accuracy check"""
    print("🎯 SMART ATTENDANCE SYSTEM - QUICK ACCURACY CHECK")
    print("="*60)
    
    # Check system status
    fr_available, photos, students = check_system_status()
    
    # Test face detection
    test_face_detection_on_photos(photos)
    
    # Test with smart system
    test_with_smart_system(photos)
    
    print(f"\n✅ Quick accuracy check completed!")
    print(f"\n💡 TIPS FOR BETTER ACCURACY:")
    print("   - Use high-quality, well-lit photos")
    print("   - Ensure faces are clearly visible")
    print("   - Add multiple photos per student")
    print("   - Install face_recognition for better recognition")

if __name__ == "__main__":
    main()

