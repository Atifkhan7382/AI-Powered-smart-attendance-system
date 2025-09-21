#!/usr/bin/env python3
"""
Quick fix for large images causing hanging
"""

import cv2
import numpy as np
import face_recognition
import os
from pathlib import Path
import time

def resize_image_if_large(image, max_size=1024):
    """Resize image if it's too large for processing"""
    height, width = image.shape[:2]
    
    if width > max_size or height > max_size:
        # Calculate new dimensions maintaining aspect ratio
        if width > height:
            new_width = max_size
            new_height = int((height * max_size) / width)
        else:
            new_height = max_size
            new_width = int((width * max_size) / height)
        
        print(f"    Resizing image from {width}x{height} to {new_width}x{new_height}")
        resized_image = cv2.resize(image, (new_width, new_height))
        return resized_image
    
    return image

def test_with_resized_image():
    """Test with resized image"""
    print("🔧 Testing with Resized Image")
    print("="*40)
    
    # Find first student image
    student_photos_dir = Path("student_photos")
    student_folders = [f for f in student_photos_dir.iterdir() if f.is_dir() and not f.name.startswith('.')]
    
    if not student_folders:
        print("❌ No student folders found")
        return False
    
    student_folder = student_folders[0]
    images = list(student_folder.glob("*.jpg")) + list(student_folder.glob("*.jpeg")) + list(student_folder.glob("*.png"))
    
    if not images:
        print("❌ No images found")
        return False
    
    test_image_path = images[0]
    print(f"📸 Testing: {test_image_path.name}")
    
    try:
        # Load image
        print("  Loading image...")
        image = face_recognition.load_image_file(str(test_image_path))
        print(f"  Original size: {image.shape}")
        
        # Resize if too large
        resized_image = resize_image_if_large(image, max_size=1024)
        
        # Test face detection
        print("  Detecting faces...")
        start_time = time.time()
        face_locations = face_recognition.face_locations(resized_image, model="hog")
        detection_time = time.time() - start_time
        print(f"  ✅ Face detection: {len(face_locations)} faces in {detection_time:.2f}s")
        
        if face_locations:
            # Test face encoding
            print("  Creating encodings...")
            start_time = time.time()
            encodings = face_recognition.face_encodings(resized_image, face_locations)
            encoding_time = time.time() - start_time
            print(f"  ✅ Face encoding: {len(encodings)} encodings in {encoding_time:.2f}s")
            
            if encodings:
                print("  🎯 SUCCESS! Face processing works with resized image")
                return True
        
        print("  ⚠️  No faces detected or encoding failed")
        return False
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def create_fixed_registration_script():
    """Create a fixed registration script"""
    print("\n🔧 Creating Fixed Registration Script")
    print("="*40)
    
    script_content = '''
import cv2
import numpy as np
import face_recognition
import os
from pathlib import Path
import time

def resize_image_if_large(image, max_size=1024):
    """Resize image if it's too large for processing"""
    height, width = image.shape[:2]
    
    if width > max_size or height > max_size:
        if width > height:
            new_width = max_size
            new_height = int((height * max_size) / width)
        else:
            new_height = max_size
            new_width = int((width * max_size) / height)
        
        print(f"    Resizing from {width}x{height} to {new_width}x{new_height}")
        return cv2.resize(image, (new_width, new_height))
    
    return image

def quick_register_students():
    """Quick student registration with image resizing"""
    print("🚀 Quick Student Registration")
    print("="*40)
    
    student_photos_dir = Path("student_photos")
    if not student_photos_dir.exists():
        print("❌ student_photos directory not found")
        return
    
    student_folders = [f for f in student_photos_dir.iterdir() if f.is_dir() and not f.name.startswith('.')]
    print(f"Found {len(student_folders)} student folders")
    
    successful = 0
    failed = 0
    
    for folder in student_folders:
        print(f"\\nProcessing {folder.name}...")
        
        # Find images
        images = list(folder.glob("*.jpg")) + list(folder.glob("*.jpeg")) + list(folder.glob("*.png"))
        
        if not images:
            print(f"  ❌ No images found")
            failed += 1
            continue
        
        print(f"  📸 Found {len(images)} images")
        
        # Process first image
        image_path = images[0]
        try:
            # Load and resize image
            image = face_recognition.load_image_file(str(image_path))
            resized_image = resize_image_if_large(image, max_size=1024)
            
            # Detect faces
            face_locations = face_recognition.face_locations(resized_image, model="hog")
            
            if face_locations:
                # Create encodings
                encodings = face_recognition.face_encodings(resized_image, face_locations)
                
                if encodings:
                    print(f"  ✅ Success: {len(encodings)} encodings created")
                    successful += 1
                else:
                    print(f"  ❌ Failed: No encodings created")
                    failed += 1
            else:
                print(f"  ❌ Failed: No faces detected")
                failed += 1
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
            failed += 1
    
    print(f"\\n📊 Results: {successful} successful, {failed} failed")

if __name__ == "__main__":
    quick_register_students()
'''
    
    with open("quick_register_fixed.py", "w") as f:
        f.write(script_content)
    
    print("✅ Created quick_register_fixed.py")
    print("Run this script to register students with proper image resizing")

def main():
    """Main function"""
    print("🔧 FIXING HANGING REGISTRATION ISSUE")
    print("="*50)
    
    # Test with resized image
    success = test_with_resized_image()
    
    if success:
        print("\n✅ SOLUTION FOUND!")
        print("The issue is large images (4000x3000) causing timeouts.")
        print("Solution: Resize images to max 1024px before processing.")
        
        # Create fixed script
        create_fixed_registration_script()
        
        print("\n💡 Next Steps:")
        print("1. Run: python quick_register_fixed.py")
        print("2. This will process all students with proper image resizing")
        print("3. The original system can be fixed by adding image resizing")
        
    else:
        print("\n❌ Issue not resolved with image resizing")
        print("There might be other problems with the face recognition setup")

if __name__ == "__main__":
    main()
