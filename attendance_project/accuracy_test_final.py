from smart_attendance_system import SmartAttendanceSystem
import cv2
from pathlib import Path
import time

print('=== ACCURACY TEST RESULTS ===')
print()

# Initialize system
print('Initializing Smart Attendance System...')
system = SmartAttendanceSystem()
print('✅ System initialized')

# Test on classroom photos
photos = list(Path('classroom_photos').glob('*.jpg'))
photos.extend(list(Path('classroom_photos').glob('*.jpeg')))
photos.extend(list(Path('classroom_photos').glob('*.png')))

print(f'Found {len(photos)} photos to test')
print()

total_faces = 0
total_time = 0
recognized_faces = 0

for photo in photos:
    print(f'Testing: {photo.name}')
    image = cv2.imread(str(photo))
    if image is not None:
        print(f'  Image size: {image.shape[1]}x{image.shape[0]}')
        
        # Test face detection
        start_time = time.time()
        results = system.detect_and_recognize_faces(image)
        detection_time = time.time() - start_time
        
        print(f'  Faces detected: {len(results)}')
        print(f'  Processing time: {detection_time:.2f}s')
        
        total_faces += len(results)
        total_time += detection_time
        
        # Show details
        for i, r in enumerate(results):
            student_id = r['student_id']
            confidence = r['confidence']
            print(f'    Face {i+1}: {student_id} (confidence: {confidence:.2f})')
            if student_id != 'Unknown':
                recognized_faces += 1
    else:
        print('  Could not load image')
    print()

# Calculate metrics
if len(photos) > 0:
    avg_faces = total_faces / len(photos)
    avg_time = total_time / len(photos)
    recognition_rate = recognized_faces / total_faces if total_faces > 0 else 0
    
    print('=== ACCURACY METRICS ===')
    print(f'Photos tested: {len(photos)}')
    print(f'Total faces detected: {total_faces}')
    print(f'Average faces per photo: {avg_faces:.1f}')
    print(f'Average processing time: {avg_time:.2f}s')
    print(f'Recognized faces: {recognized_faces}')
    print(f'Recognition rate: {recognition_rate:.1%}')
    
    # Performance ratings
    if avg_time < 1.0:
        speed_rating = '🚀 Excellent'
    elif avg_time < 2.0:
        speed_rating = '✅ Good'
    elif avg_time < 5.0:
        speed_rating = '⚠️ Average'
    else:
        speed_rating = '🐌 Slow'
    
    if avg_faces >= 2:
        detection_rating = '🎯 Excellent'
    elif avg_faces >= 1:
        detection_rating = '✅ Good'
    elif avg_faces >= 0.5:
        detection_rating = '⚠️ Average'
    else:
        detection_rating = '❌ Poor'
    
    if recognition_rate >= 0.8:
        recognition_rating = '🎯 Excellent'
    elif recognition_rate >= 0.6:
        recognition_rating = '✅ Good'
    elif recognition_rate >= 0.4:
        recognition_rating = '⚠️ Average'
    else:
        recognition_rating = '❌ Poor'
    
    print(f'Processing speed: {speed_rating}')
    print(f'Detection rate: {detection_rating}')
    print(f'Recognition accuracy: {recognition_rating}')
    
    print()
    print('=== RECOMMENDATIONS ===')
    if avg_faces < 1:
        print('• Improve image quality and lighting for better face detection')
    if recognition_rate < 0.6:
        print('• Add more student photos to improve recognition accuracy')
    if avg_time > 2:
        print('• Consider reducing image resolution for faster processing')
    if total_faces == 0:
        print('• Check if faces are clearly visible in the photos')
        print('• Try different camera angles or lighting conditions')

print('=== TEST COMPLETE ===')

