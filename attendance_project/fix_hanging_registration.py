#!/usr/bin/env python3
"""
Quick fix for hanging registration process
"""

import os
import sys
import signal
import time
from pathlib import Path

def timeout_handler(signum, frame):
    print("\n⚠️  Registration process timed out!")
    print("This might be due to:")
    print("1. Large image files taking too long to process")
    print("2. face_recognition library being slow")
    print("3. System resource constraints")
    print("\nTrying to continue with next student...")
    raise TimeoutError("Registration timeout")

def safe_face_encoding(image, face_locations, timeout_seconds=30):
    """Safe face encoding with timeout"""
    try:
        # Set timeout
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout_seconds)
        
        # Perform encoding
        encodings = face_recognition.face_encodings(image, face_locations)
        
        # Cancel timeout
        signal.alarm(0)
        
        return encodings
    except TimeoutError:
        print(f"    ⚠️  Face encoding timed out after {timeout_seconds}s")
        return []
    except Exception as e:
        print(f"    ❌ Face encoding error: {e}")
        return []

def test_single_student_registration():
    """Test registration with a single student to identify the issue"""
    print("🔍 Testing Single Student Registration")
    print("="*50)
    
    # Check if face_recognition is available
    try:
        import face_recognition
        print("✅ face_recognition library available")
    except ImportError:
        print("❌ face_recognition library not available")
        return False
    
    # Check student photos directory
    student_photos_dir = Path("student_photos")
    if not student_photos_dir.exists():
        print("❌ student_photos directory not found")
        return False
    
    # Find first student folder
    student_folders = [f for f in student_photos_dir.iterdir() if f.is_dir() and not f.name.startswith('.')]
    if not student_folders:
        print("❌ No student folders found")
        return False
    
    student_folder = student_folders[0]
    print(f"📁 Testing with folder: {student_folder.name}")
    
    # Find images in folder
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']
    images = []
    for ext in image_extensions:
        images.extend(list(student_folder.glob(ext)))
    
    if not images:
        print("❌ No images found in folder")
        return False
    
    print(f"📸 Found {len(images)} images")
    
    # Test with first image
    test_image_path = images[0]
    print(f"🖼️  Testing with: {test_image_path.name}")
    
    try:
        # Load image
        print("  Loading image...")
        image = face_recognition.load_image_file(str(test_image_path))
        print(f"  ✅ Image loaded: {image.shape}")
        
        # Detect faces
        print("  Detecting faces...")
        start_time = time.time()
        face_locations = face_recognition.face_locations(image, model="hog")
        detection_time = time.time() - start_time
        print(f"  ✅ Face detection completed in {detection_time:.2f}s")
        print(f"  🎯 Found {len(face_locations)} faces")
        
        if not face_locations:
            print("  ⚠️  No faces detected - this might be the issue")
            return False
        
        # Test face encoding with timeout
        print("  Creating face encodings...")
        start_time = time.time()
        encodings = safe_face_encoding(image, face_locations, timeout_seconds=30)
        encoding_time = time.time() - start_time
        
        if encodings:
            print(f"  ✅ Face encoding completed in {encoding_time:.2f}s")
            print(f"  🎯 Created {len(encodings)} encodings")
            return True
        else:
            print("  ❌ Face encoding failed or timed out")
            return False
            
    except Exception as e:
        print(f"  ❌ Error during testing: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Quick Fix for Hanging Registration")
    print("="*50)
    
    # Test single student registration
    success = test_single_student_registration()
    
    if success:
        print("\n✅ Single student registration works!")
        print("The issue might be with batch processing or large images.")
        print("\n💡 Recommendations:")
        print("1. Try processing students one by one")
        print("2. Reduce image sizes if they're very large")
        print("3. Use 'hog' model instead of 'cnn' for faster processing")
    else:
        print("\n❌ Single student registration failed!")
        print("The issue is with the basic face recognition process.")
        print("\n💡 Recommendations:")
        print("1. Check image quality and lighting")
        print("2. Ensure faces are clearly visible")
        print("3. Try with different images")
        print("4. Check if face_recognition library is properly installed")

if __name__ == "__main__":
    main()
