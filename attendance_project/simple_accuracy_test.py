import cv2
import numpy as np
import os
import time
from datetime import datetime
from pathlib import Path
from smart_attendance_system import SmartAttendanceSystem

def test_face_detection_accuracy():
    """Simple face detection accuracy test"""
    print("🔍 Testing Face Detection Accuracy...")
    print("="*50)
    
    # Initialize system
    system = SmartAttendanceSystem()
    
    # Test on classroom photos
    classroom_photos = list(Path("classroom_photos").glob("*.jpg"))
    classroom_photos.extend(list(Path("classroom_photos").glob("*.jpeg")))
    classroom_photos.extend(list(Path("classroom_photos").glob("*.png")))
    
    total_images = 0
    total_faces = 0
    total_processing_time = 0
    confidence_scores = []
    
    print(f"Found {len(classroom_photos)} classroom photos to test")
    
    for photo_path in classroom_photos:
        if photo_path.exists():
            print(f"\n📸 Testing: {photo_path.name}")
            
            # Load image
            image = cv2.imread(str(photo_path))
            if image is None:
                print(f"   ❌ Could not load image")
                continue
            
            print(f"   📏 Image size: {image.shape[1]}x{image.shape[0]}")
            
            # Test face detection
            start_time = time.time()
            detection_results = system.detect_and_recognize_faces(image)
            processing_time = time.time() - start_time
            
            total_images += 1
            total_faces += len(detection_results)
            total_processing_time += processing_time
            
            # Collect confidence scores
            for result in detection_results:
                confidence_scores.append(result['confidence'])
            
            print(f"   ✅ Found {len(detection_results)} faces")
            print(f"   ⏱️  Processing time: {processing_time:.2f}s")
            
            # Show detection details
            for i, result in enumerate(detection_results):
                student_id = result['student_id']
                confidence = result['confidence']
                bbox = result['bounding_box']
                print(f"      Face {i+1}: {student_id} (confidence: {confidence:.2f})")
                print(f"                Bounding box: {bbox}")
    
    # Calculate metrics
    if total_images > 0:
        avg_faces_per_image = total_faces / total_images
        avg_processing_time = total_processing_time / total_images
        avg_confidence = np.mean(confidence_scores) if confidence_scores else 0
        
        print(f"\n📊 ACCURACY METRICS:")
        print(f"   Images tested: {total_images}")
        print(f"   Total faces detected: {total_faces}")
        print(f"   Average faces per image: {avg_faces_per_image:.2f}")
        print(f"   Average processing time: {avg_processing_time:.2f}s")
        print(f"   Average confidence: {avg_confidence:.2f}")
        
        # Performance rating
        if avg_processing_time < 1.0:
            speed_rating = "🚀 Excellent"
        elif avg_processing_time < 2.0:
            speed_rating = "✅ Good"
        elif avg_processing_time < 5.0:
            speed_rating = "⚠️  Average"
        else:
            speed_rating = "🐌 Slow"
        
        print(f"   Processing speed: {speed_rating}")
        
        # Detection rating
        if avg_faces_per_image > 2:
            detection_rating = "🎯 Excellent"
        elif avg_faces_per_image > 1:
            detection_rating = "✅ Good"
        elif avg_faces_per_image > 0.5:
            detection_rating = "⚠️  Average"
        else:
            detection_rating = "❌ Poor"
        
        print(f"   Detection rate: {detection_rating}")
        
        # Confidence rating
        if avg_confidence > 0.8:
            conf_rating = "🎯 Excellent"
        elif avg_confidence > 0.6:
            conf_rating = "✅ Good"
        elif avg_confidence > 0.4:
            conf_rating = "⚠️  Average"
        else:
            conf_rating = "❌ Poor"
        
        print(f"   Confidence level: {conf_rating}")
        
        return {
            'total_images': total_images,
            'total_faces': total_faces,
            'avg_faces_per_image': avg_faces_per_image,
            'avg_processing_time': avg_processing_time,
            'avg_confidence': avg_confidence,
            'speed_rating': speed_rating,
            'detection_rating': detection_rating,
            'confidence_rating': conf_rating
        }
    else:
        print("❌ No images found to test")
        return None

def test_recognition_accuracy():
    """Test face recognition accuracy"""
    print(f"\n🎯 Testing Face Recognition Accuracy...")
    print("="*50)
    
    # Check if face_recognition is available
    try:
        import face_recognition
        print("✅ face_recognition library available")
        
        system = SmartAttendanceSystem()
        
        # Check how many students we have encodings for
        print(f"📚 Students in database: {len(system.known_face_names)}")
        print(f"📚 Face encodings available: {len(system.known_face_encodings)}")
        
        if len(system.known_face_names) > 0:
            print("✅ Face recognition is ready")
            print("   Students with encodings:")
            for i, name in enumerate(system.known_face_names):
                print(f"      {i+1}. {name}")
        else:
            print("⚠️  No face encodings available")
            print("   Add student photos to 'student_database/' folder")
            print("   Structure: student_database/student_id/photo1.jpg")
        
        return True
    except ImportError:
        print("❌ face_recognition library not available")
        print("   Using OpenCV face detection only")
        return False

def test_database_health():
    """Test database health and data integrity"""
    print(f"\n🗄️  Testing Database Health...")
    print("="*50)
    
    system = SmartAttendanceSystem()
    
    # Connect to database
    import sqlite3
    conn = sqlite3.connect(system.database_file)
    cursor = conn.cursor()
    
    # Count records
    cursor.execute("SELECT COUNT(*) FROM students")
    student_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM attendance")
    attendance_count = cursor.fetchone()[0]
    
    # Test data integrity
    cursor.execute("PRAGMA integrity_check")
    integrity_result = cursor.fetchone()[0]
    
    conn.close()
    
    print(f"📊 Students in database: {student_count}")
    print(f"📊 Attendance records: {attendance_count}")
    print(f"📊 Database integrity: {'✅ OK' if integrity_result == 'ok' else '❌ Issues'}")
    
    # Health rating
    if student_count > 0 and integrity_result == 'ok':
        health_rating = "✅ Healthy"
    elif student_count > 0:
        health_rating = "⚠️  Needs attention"
    else:
        health_rating = "❌ Empty/Corrupted"
    
    print(f"📊 Database health: {health_rating}")
    
    return {
        'student_count': student_count,
        'attendance_count': attendance_count,
        'integrity': integrity_result == 'ok',
        'health_rating': health_rating
    }

def generate_recommendations(results):
    """Generate recommendations based on test results"""
    print(f"\n💡 RECOMMENDATIONS:")
    print("="*50)
    
    recommendations = []
    
    if results['detection']:
        detection = results['detection']
        
        if detection['avg_faces_per_image'] < 1:
            recommendations.append("🔍 Improve face detection:")
            recommendations.append("   - Check image quality and lighting")
            recommendations.append("   - Ensure faces are clearly visible")
            recommendations.append("   - Try different camera angles")
        
        if detection['avg_processing_time'] > 2:
            recommendations.append("⚡ Improve processing speed:")
            recommendations.append("   - Reduce image resolution")
            recommendations.append("   - Use GPU acceleration if available")
            recommendations.append("   - Consider using 'hog' model instead of 'cnn'")
        
        if detection['avg_confidence'] < 0.6:
            recommendations.append("🎯 Improve detection confidence:")
            recommendations.append("   - Adjust tolerance settings")
            recommendations.append("   - Improve image quality")
            recommendations.append("   - Ensure good lighting conditions")
    
    if results['recognition']:
        recommendations.append("🎯 Face recognition is available")
        recommendations.append("   - Add more student photos for better accuracy")
        recommendations.append("   - Use multiple angles per student")
    else:
        recommendations.append("📚 Install face_recognition library:")
        recommendations.append("   - Run: pip install face_recognition")
        recommendations.append("   - This will enable face recognition features")
    
    if results['database']:
        db = results['database']
        if db['student_count'] == 0:
            recommendations.append("👥 Add students to database:")
            recommendations.append("   - Use database_init.py to add sample students")
            recommendations.append("   - Add student photos to student_database/")
    
    for rec in recommendations:
        print(rec)

def main():
    """Run all accuracy tests"""
    print("🎯 SMART ATTENDANCE SYSTEM - ACCURACY TEST")
    print("="*60)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    # Test 1: Face Detection
    results['detection'] = test_face_detection_accuracy()
    
    # Test 2: Face Recognition
    results['recognition'] = test_recognition_accuracy()
    
    # Test 3: Database Health
    results['database'] = test_database_health()
    
    # Generate recommendations
    generate_recommendations(results)
    
    print(f"\n✅ Accuracy testing completed!")
    print(f"Test finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()

