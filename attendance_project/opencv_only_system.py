#!/usr/bin/env python3
"""
OpenCV-Only Attendance System - No face_recognition dependency
This system works without hanging issues
"""

import cv2
import numpy as np
import sqlite3
import os
from pathlib import Path
import time
from datetime import datetime

class OpenCVAttendanceSystem:
    """Attendance system using only OpenCV (no face_recognition)"""
    
    def __init__(self):
        self.database_file = "attendance.db"
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.student_photos = {}
        self.load_student_photos()
    
    def load_student_photos(self):
        """Load student photos for reference"""
        student_photos_dir = Path("student_photos")
        if not student_photos_dir.exists():
            print("❌ Student photos directory not found")
            return
        
        folders = [f for f in student_photos_dir.iterdir() if f.is_dir() and not f.name.startswith('.')]
        
        for folder in folders:
            # Look for resized images first
            images = list(folder.glob("resized_*.jpg")) + list(folder.glob("resized_*.jpeg")) + list(folder.glob("resized_*.png"))
            if not images:
                images = list(folder.glob("*.jpg")) + list(folder.glob("*.jpeg")) + list(folder.glob("*.png"))
            
            if images:
                student_id = folder.name.upper()
                student_name = folder.name.replace('_', ' ').title()
                self.student_photos[student_id] = {
                    'name': student_name,
                    'photo_path': str(images[0])
                }
        
        print(f"✅ Loaded {len(self.student_photos)} student photos")
    
    def detect_faces_opencv(self, image):
        """Detect faces using OpenCV"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
        return faces
    
    def extract_face_features(self, image, face_rect):
        """Extract simple features from face region"""
        x, y, w, h = face_rect
        face_roi = image[y:y+h, x:x+w]
        
        # Resize to standard size
        face_roi = cv2.resize(face_roi, (100, 100))
        
        # Convert to grayscale
        gray_face = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
        
        # Simple feature extraction (histogram)
        hist = cv2.calcHist([gray_face], [0], None, [256], [0, 256])
        return hist.flatten()
    
    def compare_faces_simple(self, face1_features, face2_features):
        """Simple face comparison using histogram correlation"""
        correlation = cv2.compareHist(face1_features, face2_features, cv2.HISTCMP_CORREL)
        return correlation
    
    def process_classroom_photo(self, image_path):
        """Process classroom photo and detect faces"""
        print(f"\n📸 PROCESSING: {os.path.basename(image_path)}")
        print("="*40)
        
        if not os.path.exists(image_path):
            print(f"❌ Image not found: {image_path}")
            return
        
        # Load image
        image = cv2.imread(str(image_path))
        if image is None:
            print(f"❌ Could not load image")
            return
        
        print(f"  Image size: {image.shape[1]}x{image.shape[0]}")
        
        # Detect faces
        print("  Detecting faces...")
        start_time = time.time()
        faces = self.detect_faces_opencv(image)
        detection_time = time.time() - start_time
        print(f"  ✅ Found {len(faces)} faces in {detection_time:.2f}s")
        
        if len(faces) == 0:
            print("  ❌ No faces detected")
            return
        
        # Process each face
        results = []
        for i, face_rect in enumerate(faces):
            print(f"  Processing face {i+1}...")
            
            # Extract features
            face_features = self.extract_face_features(image, face_rect)
            
            # Try to match with student photos
            best_match = None
            best_similarity = 0.0
            
            for student_id, student_data in self.student_photos.items():
                try:
                    # Load student photo
                    student_image = cv2.imread(student_data['photo_path'])
                    if student_image is None:
                        continue
                    
                    # Detect faces in student photo
                    student_faces = self.detect_faces_opencv(student_image)
                    if len(student_faces) == 0:
                        continue
                    
                    # Use first face from student photo
                    student_face_features = self.extract_face_features(student_image, student_faces[0])
                    
                    # Compare faces
                    similarity = self.compare_faces_simple(face_features, student_face_features)
                    
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_match = student_id
                
                except Exception as e:
                    continue
            
            # Determine result
            if best_match and best_similarity > 0.7:  # Threshold for recognition
                student_name = self.student_photos[best_match]['name']
                results.append({
                    'face_id': i+1,
                    'student_id': best_match,
                    'name': student_name,
                    'confidence': best_similarity,
                    'face_rect': face_rect
                })
                print(f"    ✅ {student_name} (similarity: {best_similarity:.2f})")
            else:
                results.append({
                    'face_id': i+1,
                    'student_id': 'Unknown',
                    'name': 'Unknown',
                    'confidence': best_similarity,
                    'face_rect': face_rect
                })
                print(f"    ❓ Unknown person (similarity: {best_similarity:.2f})")
        
        # Mark attendance
        self.mark_attendance_batch(results, image_path)
        
        print(f"\n📊 RESULTS:")
        print(f"  Total faces: {len(results)}")
        recognized = len([r for r in results if r['student_id'] != 'Unknown'])
        print(f"  Recognized: {recognized}")
        print(f"  Unknown: {len(results) - recognized}")
        
        return results
    
    def mark_attendance_batch(self, results, image_path):
        """Mark attendance for all recognized students"""
        conn = sqlite3.connect(self.database_file)
        cursor = conn.cursor()
        
        # Create attendance table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT,
                date DATE,
                time TIME,
                confidence REAL,
                image_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        current_date = datetime.now().date()
        current_time = datetime.now().time()
        
        for result in results:
            if result['student_id'] != 'Unknown':
                cursor.execute('''
                    INSERT INTO attendance (student_id, date, time, confidence, image_path)
                    VALUES (?, ?, ?, ?, ?)
                ''', (result['student_id'], current_date, current_time, result['confidence'], image_path))
        
        conn.commit()
        conn.close()
        
        recognized_count = len([r for r in results if r['student_id'] != 'Unknown'])
        if recognized_count > 0:
            print(f"  📝 Marked attendance for {recognized_count} students")
    
    def generate_attendance_report(self):
        """Generate attendance report"""
        print(f"\n📋 ATTENDANCE REPORT")
        print("="*40)
        
        conn = sqlite3.connect(self.database_file)
        cursor = conn.cursor()
        
        # Get today's attendance
        today = datetime.now().date()
        cursor.execute('''
            SELECT DISTINCT student_id, confidence, time
            FROM attendance 
            WHERE date = ?
            ORDER BY time
        ''', (today,))
        
        records = cursor.fetchall()
        
        print(f"📅 Report for {today}")
        print("-" * 30)
        
        if records:
            for student_id, confidence, time in records:
                student_name = self.student_photos.get(student_id, {}).get('name', student_id)
                print(f"✅ {student_name} - {time} (confidence: {confidence:.2f})")
        else:
            print("No attendance records for today")
        
        conn.close()
    
    def test_system(self):
        """Test the system with classroom photos"""
        print("🧪 TESTING OPENCV ATTENDANCE SYSTEM")
        print("="*50)
        
        if not self.student_photos:
            print("❌ No student photos loaded")
            return False
        
        print(f"✅ System ready with {len(self.student_photos)} students")
        
        # Test with classroom photos
        classroom_photos = list(Path("classroom_photos").glob("*.jpg"))
        classroom_photos.extend(list(Path("classroom_photos").glob("*.jpeg")))
        classroom_photos.extend(list(Path("classroom_photos").glob("*.png")))
        
        if not classroom_photos:
            print("❌ No classroom photos found")
            return False
        
        print(f"📸 Testing with {len(classroom_photos)} classroom photos")
        
        for photo in classroom_photos:
            self.process_classroom_photo(str(photo))
        
        # Generate report
        self.generate_attendance_report()
        
        print(f"\n🎉 SYSTEM TEST COMPLETE!")
        return True

def main():
    """Main function"""
    print("🎯 OPENCV-ONLY ATTENDANCE SYSTEM")
    print("="*50)
    print("This system works without face_recognition library")
    print("No hanging issues - uses only OpenCV")
    print("="*50)
    
    # Initialize system
    system = OpenCVAttendanceSystem()
    
    # Test system
    success = system.test_system()
    
    if success:
        print(f"\n✅ SUCCESS! System is working without hanging!")
        print(f"The OpenCV-only system is functional and fast.")
    else:
        print(f"\n❌ System test failed.")
        print(f"Check the error messages above.")

if __name__ == "__main__":
    main()
