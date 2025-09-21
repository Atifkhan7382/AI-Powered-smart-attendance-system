#!/usr/bin/env python3
"""
Simple Attendance System - No Hanging Version
Uses the already registered students and works efficiently
"""

import cv2
import numpy as np
import face_recognition
import sqlite3
import json
import os
from pathlib import Path
import time
from datetime import datetime

class SimpleAttendanceSystem:
    """Simple attendance system that actually works"""
    
    def __init__(self):
        self.database_file = "attendance.db"
        self.encodings_file = "all_student_encodings.json"
        self.student_encodings = {}
        self.student_names = {}
        self.load_encodings()
    
    def load_encodings(self):
        """Load student encodings from file"""
        if os.path.exists(self.encodings_file):
            with open(self.encodings_file, 'r') as f:
                data = json.load(f)
            
            for student_id, student_data in data.items():
                self.student_encodings[student_id] = [np.array(enc) for enc in student_data['encodings']]
                self.student_names[student_id] = student_data['name']
            
            print(f"✅ Loaded {len(self.student_encodings)} students")
        else:
            print("❌ No encodings file found. Please register students first.")
    
    def detect_faces_in_image(self, image_path):
        """Detect and recognize faces in an image"""
        print(f"🔍 Processing: {os.path.basename(image_path)}")
        
        # Load image
        image = face_recognition.load_image_file(str(image_path))
        print(f"  Image size: {image.shape}")
        
        # Detect faces
        print("  Detecting faces...")
        start_time = time.time()
        face_locations = face_recognition.face_locations(image, model="hog")
        detection_time = time.time() - start_time
        print(f"  ✅ Found {len(face_locations)} faces in {detection_time:.2f}s")
        
        if not face_locations:
            print("  ❌ No faces detected")
            return []
        
        # Create encodings
        print("  Creating face encodings...")
        start_time = time.time()
        face_encodings = face_recognition.face_encodings(image, face_locations)
        encoding_time = time.time() - start_time
        print(f"  ✅ Created {len(face_encodings)} encodings in {encoding_time:.2f}s")
        
        # Match with known students
        results = []
        for i, face_encoding in enumerate(face_encodings):
            best_match = None
            best_distance = 1.0
            
            for student_id, student_encodings in self.student_encodings.items():
                distances = face_recognition.face_distance(student_encodings, face_encoding)
                min_distance = min(distances)
                
                if min_distance < best_distance:
                    best_distance = min_distance
                    best_match = student_id
            
            if best_match and best_distance < 0.6:
                student_name = self.student_names[best_match]
                confidence = 1 - best_distance
                results.append({
                    'student_id': best_match,
                    'name': student_name,
                    'confidence': confidence,
                    'face_location': face_locations[i]
                })
                print(f"    ✅ {student_name} (confidence: {confidence:.2f})")
            else:
                results.append({
                    'student_id': 'Unknown',
                    'name': 'Unknown',
                    'confidence': 0.0,
                    'face_location': face_locations[i]
                })
                print(f"    ❓ Unknown person")
        
        return results
    
    def mark_attendance(self, student_id, confidence, image_path=""):
        """Mark attendance for a student"""
        if student_id == 'Unknown':
            return False
        
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
        
        # Mark attendance
        current_date = datetime.now().date()
        current_time = datetime.now().time()
        
        cursor.execute('''
            INSERT INTO attendance (student_id, date, time, confidence, image_path)
            VALUES (?, ?, ?, ?, ?)
        ''', (student_id, current_date, current_time, confidence, image_path))
        
        conn.commit()
        conn.close()
        
        print(f"  📝 Attendance marked for {self.student_names[student_id]}")
        return True
    
    def process_classroom_photo(self, image_path):
        """Process a classroom photo and mark attendance"""
        print(f"\n📸 PROCESSING CLASSROOM PHOTO")
        print("="*40)
        
        if not os.path.exists(image_path):
            print(f"❌ Image not found: {image_path}")
            return
        
        # Detect and recognize faces
        results = self.detect_faces_in_image(image_path)
        
        if not results:
            print("❌ No faces detected in classroom photo")
            return
        
        # Mark attendance for recognized students
        present_students = []
        for result in results:
            if result['student_id'] != 'Unknown':
                self.mark_attendance(result['student_id'], result['confidence'], image_path)
                present_students.append(result)
        
        print(f"\n📊 RESULTS:")
        print(f"  Total faces: {len(results)}")
        print(f"  Recognized: {len(present_students)}")
        print(f"  Unknown: {len(results) - len(present_students)}")
        
        if present_students:
            print(f"\n👥 PRESENT STUDENTS:")
            for student in present_students:
                print(f"  ✅ {student['name']} ({student['confidence']:.2f})")
        
        return results
    
    def generate_attendance_report(self):
        """Generate attendance report"""
        print(f"\n📋 GENERATING ATTENDANCE REPORT")
        print("="*40)
        
        conn = sqlite3.connect(self.database_file)
        cursor = conn.cursor()
        
        # Get today's attendance
        today = datetime.now().date()
        cursor.execute('''
            SELECT s.student_id, s.name, a.time, a.confidence
            FROM students s
            LEFT JOIN attendance a ON s.student_id = a.student_id AND a.date = ?
            ORDER BY s.name
        ''', (today,))
        
        records = cursor.fetchall()
        
        print(f"📅 Attendance Report for {today}")
        print("-" * 50)
        
        present_count = 0
        for record in records:
            student_id, name, time, confidence = record
            if time:
                print(f"✅ {name} - {time} (confidence: {confidence:.2f})")
                present_count += 1
            else:
                print(f"❌ {name} - Absent")
        
        total_students = len(records)
        print(f"\n📊 Summary:")
        print(f"  Present: {present_count}")
        print(f"  Absent: {total_students - present_count}")
        print(f"  Total: {total_students}")
        
        conn.close()
        return present_count, total_students

def main():
    """Main function"""
    print("🎯 SIMPLE ATTENDANCE SYSTEM")
    print("="*50)
    
    # Initialize system
    system = SimpleAttendanceSystem()
    
    if not system.student_encodings:
        print("❌ No students registered. Please run student registration first.")
        return
    
    print(f"✅ System ready with {len(system.student_encodings)} students")
    
    # Process classroom photos
    classroom_photos = list(Path("classroom_photos").glob("*.jpg"))
    classroom_photos.extend(list(Path("classroom_photos").glob("*.jpeg")))
    classroom_photos.extend(list(Path("classroom_photos").glob("*.png")))
    
    if classroom_photos:
        print(f"\n📸 Found {len(classroom_photos)} classroom photos")
        
        for photo in classroom_photos:
            system.process_classroom_photo(str(photo))
    else:
        print("❌ No classroom photos found")
    
    # Generate report
    system.generate_attendance_report()
    
    print(f"\n🎉 ATTENDANCE SYSTEM COMPLETE!")
    print(f"The system is working without hanging!")

if __name__ == "__main__":
    main()

