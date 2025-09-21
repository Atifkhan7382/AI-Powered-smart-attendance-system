#!/usr/bin/env python3
"""
Fix for hanging registration - resizes large images before processing
"""

import cv2
import numpy as np
import os
from pathlib import Path
import time

def resize_image_for_processing(image_path, max_size=1024):
    """Resize image to reasonable size for face recognition"""
    print(f"  Processing: {os.path.basename(image_path)}")
    
    # Load image with OpenCV
    image = cv2.imread(str(image_path))
    if image is None:
        print(f"    ❌ Could not load image")
        return None
    
    height, width = image.shape[:2]
    print(f"    Original size: {width}x{height}")
    
    # Resize if too large
    if width > max_size or height > max_size:
        if width > height:
            new_width = max_size
            new_height = int((height * max_size) / width)
        else:
            new_height = max_size
            new_width = int((width * max_size) / height)
        
        print(f"    Resizing to: {new_width}x{new_height}")
        resized_image = cv2.resize(image, (new_width, new_height))
        
        # Save resized image
        resized_path = image_path.parent / f"resized_{image_path.name}"
        cv2.imwrite(str(resized_path), resized_image)
        print(f"    ✅ Saved resized image: {resized_path.name}")
        
        return str(resized_path)
    else:
        print(f"    ✅ Image size OK, no resizing needed")
        return str(image_path)

def process_all_student_images():
    """Process all student images and resize if needed"""
    print("🔧 FIXING LARGE IMAGES FOR REGISTRATION")
    print("="*50)
    
    student_photos_dir = Path("student_photos")
    if not student_photos_dir.exists():
        print("❌ student_photos directory not found")
        return
    
    student_folders = [f for f in student_photos_dir.iterdir() if f.is_dir() and not f.name.startswith('.')]
    print(f"Found {len(student_folders)} student folders")
    
    total_processed = 0
    total_resized = 0
    
    for folder in student_folders:
        print(f"\n📁 Processing folder: {folder.name}")
        
        # Find all images
        image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']
        images = []
        for ext in image_extensions:
            images.extend(list(folder.glob(ext)))
        
        if not images:
            print(f"  ❌ No images found")
            continue
        
        print(f"  📸 Found {len(images)} images")
        
        for image_path in images:
            # Skip already resized images
            if image_path.name.startswith('resized_'):
                continue
            
            result = resize_image_for_processing(image_path)
            if result:
                total_processed += 1
                if 'resized_' in result:
                    total_resized += 1
    
    print(f"\n📊 SUMMARY:")
    print(f"  Total images processed: {total_processed}")
    print(f"  Images resized: {total_resized}")
    print(f"  Images already OK: {total_processed - total_resized}")
    
    if total_resized > 0:
        print(f"\n✅ FIXED! Large images have been resized.")
        print(f"Now you can run the registration process safely.")
    else:
        print(f"\n✅ All images were already the right size.")

def create_quick_test_script():
    """Create a quick test script for registration"""
    print(f"\n🧪 Creating quick test script...")
    
    test_script = '''#!/usr/bin/env python3
"""
Quick test for student registration with resized images
"""

import cv2
import numpy as np
import face_recognition
import os
from pathlib import Path
import time

def test_single_student():
    """Test registration with a single student"""
    print("🧪 Testing Single Student Registration")
    print("="*40)
    
    # Find first student folder
    student_photos_dir = Path("student_photos")
    student_folders = [f for f in student_photos_dir.iterdir() if f.is_dir() and not f.name.startswith('.')]
    
    if not student_folders:
        print("❌ No student folders found")
        return False
    
    folder = student_folders[0]
    print(f"Testing folder: {folder.name}")
    
    # Find resized images first, then original
    images = list(folder.glob("resized_*.jpg")) + list(folder.glob("resized_*.jpeg")) + list(folder.glob("resized_*.png"))
    if not images:
        images = list(folder.glob("*.jpg")) + list(folder.glob("*.jpeg")) + list(folder.glob("*.png"))
    
    if not images:
        print("❌ No images found")
        return False
    
    image_path = images[0]
    print(f"Testing image: {image_path.name}")
    
    try:
        # Load image
        print("  Loading image...")
        image = face_recognition.load_image_file(str(image_path))
        print(f"  Image size: {image.shape}")
        
        # Detect faces
        print("  Detecting faces...")
        start_time = time.time()
        face_locations = face_recognition.face_locations(image, model="hog")
        detection_time = time.time() - start_time
        print(f"  ✅ Found {len(face_locations)} faces in {detection_time:.2f}s")
        
        if face_locations:
            # Create encodings
            print("  Creating face encodings...")
            start_time = time.time()
            encodings = face_recognition.face_encodings(image, face_locations)
            encoding_time = time.time() - start_time
            print(f"  ✅ Created {len(encodings)} encodings in {encoding_time:.2f}s")
            
            if encodings:
                print("  🎯 SUCCESS! Registration should work now.")
                return True
        
        print("  ⚠️  No faces detected or encoding failed")
        return False
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_single_student()
    if success:
        print("\\n✅ Registration test passed!")
        print("You can now run the full registration process.")
    else:
        print("\\n❌ Registration test failed.")
        print("Check image quality and try again.")
'''
    
    with open("test_registration.py", "w") as f:
        f.write(test_script)
    
    print("✅ Created test_registration.py")

def main():
    """Main function"""
    print("🚀 FIXING REGISTRATION HANGING ISSUE")
    print("="*50)
    
    # Process all images
    process_all_student_images()
    
    # Create test script
    create_quick_test_script()
    
    print(f"\n🎯 NEXT STEPS:")
    print(f"1. Run: python test_registration.py")
    print(f"2. If test passes, run the original registration")
    print(f"3. The system should now work without hanging")

if __name__ == "__main__":
    main()
