import cv2
import numpy as np
import face_recognition
import os
import pickle
import pandas as pd
from datetime import datetime, date
import json
import logging
from typing import List, Dict, Tuple, Optional
from PIL import Image, ImageEnhance
import warnings
import glob
from pathlib import Path
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
warnings.filterwarnings("ignore")

class OptimizedAttendanceSystem:
    """
    Optimized Smart Attendance System with precomputed encodings support
    """
    
    def __init__(self, base_path: str = None):
        """
        Initialize the attendance system with optimized settings
        """
        # Use the exact path from your system
        if base_path is None:
            self.base_path = "C:/Users/atifk/Desktop/Attendence/attendance_project"
        else:
            self.base_path = base_path
            
        # Setup directory paths
        self.student_data_path = os.path.join(self.base_path, "student_data")
        self.attendance_path = os.path.join(self.base_path, "attendance_records")
        self.models_path = os.path.join(self.base_path, "models")
        self.logs_path = os.path.join(self.base_path, "logs")
        self.batch_images_path = os.path.join(self.base_path, "student_photos")
        self.classroom_images_path = os.path.join(self.base_path, "classroom_photos")
        
        # Create all necessary directories
        for path in [self.student_data_path, self.attendance_path, self.models_path, 
                     self.logs_path, self.batch_images_path, self.classroom_images_path]:
            os.makedirs(path, exist_ok=True)
        
        # Balanced parameters for accuracy and speed
        self.face_detection_model = "hog"
        self.face_recognition_tolerance = 0.5  # More strict for better accuracy
        self.min_face_size = 35  # Balanced size for accuracy
        self.max_image_width = 800  # Larger for better accuracy
        self.batch_size = 5
        self.encoding_timeout = 8  # Balanced timeout
        self.max_workers = 4  # For parallel processing
        
        # Data structures
        self.known_face_encodings = []
        self.known_face_names = []
        self.student_database = {}
        
        # Setup logging
        log_file = os.path.join(self.logs_path, f"attendance_{date.today()}.log")
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Load existing student database
        self.load_student_database()
        
        self.logger.info("Optimized Smart Attendance System initialized")
        self.logger.info(f"Base directory: {self.base_path}")
        self.logger.info(f"Loaded {len(self.student_database)} students from database")
    
    def load_precomputed_encodings(self):
        """
        Load precomputed encodings from JSON files if available (only proper names)
        """
        encodings_path = os.path.join(self.models_path, "precomputed_encodings")
        if not os.path.exists(encodings_path):
            return False
        
        encoding_files = glob.glob(os.path.join(encodings_path, "*.json"))
        if not encoding_files:
            return False
        
        loaded_count = 0
        for encoding_file in encoding_files:
            try:
                filename = os.path.basename(encoding_file)
                # Skip old generic student files
                if filename.startswith('STUDENT_'):
                    self.logger.debug(f"Skipping old generic file: {filename}")
                    continue
                
                with open(encoding_file, 'r') as f:
                    data = json.load(f)
                
                student_id = os.path.splitext(filename)[0]
                if student_id not in self.student_database:
                    # Convert list back to numpy arrays
                    encodings = [np.array(enc) for enc in data['encodings']]
                    
                    self.student_database[student_id] = {
                        'name': data['name'],
                        'encodings': encodings,
                        'registered_date': data.get('registered_date', datetime.now().isoformat()),
                        'image_count': data.get('image_count', len(encodings)),
                        'total_encodings': len(encodings)
                    }
                    
                    # Update known faces
                    self.known_face_encodings.extend(encodings)
                    self.known_face_names.extend([student_id] * len(encodings))
                    
                    loaded_count += 1
                    self.logger.info(f"Loaded proper name student: {data['name']} (ID: {student_id})")
                    
            except Exception as e:
                self.logger.error(f"Error loading precomputed encoding {encoding_file}: {str(e)}")
        
        if loaded_count > 0:
            self.logger.info(f"Loaded {loaded_count} students with proper names from precomputed encodings")
            return True
        
        return False
    
    def save_precomputed_encoding(self, student_id: str, encoding_data: Dict):
        """
        Save encoding data to JSON file for faster loading in the future
        """
        try:
            encodings_path = os.path.join(self.models_path, "precomputed_encodings")
            os.makedirs(encodings_path, exist_ok=True)
            
            encoding_file = os.path.join(encodings_path, f"{student_id}.json")
            
            # Convert numpy arrays to lists for JSON serialization
            data_to_save = encoding_data.copy()
            data_to_save['encodings'] = [enc.tolist() for enc in data_to_save['encodings']]
            
            with open(encoding_file, 'w') as f:
                json.dump(data_to_save, f, indent=2)
                
            self.logger.debug(f"Saved precomputed encoding for {student_id}")
            
        except Exception as e:
            self.logger.error(f"Error saving precomputed encoding for {student_id}: {str(e)}")
    
    def verify_system_setup(self):
        """
        Verify system setup and paths
        """
        print("=== System Setup Verification ===")
        print(f"Base directory: {self.base_path}")
        print(f"Base directory exists: {os.path.exists(self.base_path)}")
        
        directories = {
            "Student photos": self.batch_images_path,
            "Classroom photos": self.classroom_images_path,
            "Student data": self.student_data_path,
            "Attendance records": self.attendance_path,
            "Models": self.models_path,
            "Logs": self.logs_path
        }
        
        for name, path in directories.items():
            exists = os.path.exists(path)
            print(f"{name}: {exists} ({path})")
            
            if exists and name in ["Student photos", "Classroom photos"]:
                files = os.listdir(path)
                print(f"  Files/folders: {len(files)} items")
                if files:
                    print(f"  Examples: {files[:3]}")
        
        print(f"\nRegistered students: {len(self.student_database)}")
        print(f"Face encodings: {len(self.known_face_encodings)}")
        
        # Check for precomputed encodings
        encodings_path = os.path.join(self.models_path, "precomputed_encodings")
        if os.path.exists(encodings_path):
            encoding_files = glob.glob(os.path.join(encodings_path, "*.json"))
            print(f"Precomputed encodings: {len(encoding_files)} files")
        
        return True
    
    def fast_face_detection(self, image: np.ndarray) -> List[Tuple]:
        """
        Balanced face detection optimized for accuracy and speed
        """
        all_faces = []
        
        # Method 1: HOG detection (good accuracy, reasonable speed)
        try:
            hog_faces = face_recognition.face_locations(
                image, 
                number_of_times_to_upsample=1,  # Some upsampling for better accuracy
                model="hog"
            )
            if hog_faces:
                all_faces.extend(hog_faces)
                self.logger.debug(f"HOG detected {len(hog_faces)} faces")
        except Exception as e:
            self.logger.debug(f"HOG detection failed: {str(e)}")
        
        # Method 2: OpenCV Haar Cascades (good for group photos)
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            
            # More accurate detection parameters
            opencv_faces = face_cascade.detectMultiScale(
                gray, 
                scaleFactor=1.05,  # More sensitive
                minNeighbors=4,    # More strict for accuracy
                minSize=(self.min_face_size, self.min_face_size),
                maxSize=(400, 400),  # Allow larger faces
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            
            if len(opencv_faces) > 0:
                opencv_locations = [(y, x + w, y + h, x) for (x, y, w, h) in opencv_faces]
                all_faces.extend(opencv_locations)
                self.logger.debug(f"OpenCV detected {len(opencv_faces)} faces")
                
        except Exception as e:
            self.logger.debug(f"OpenCV detection failed: {str(e)}")
        
        # Combine and validate all detected faces
        if all_faces:
            unique_faces = self.remove_duplicate_faces(all_faces)
            validated_faces = self.filter_and_validate_faces(unique_faces)
            self.logger.info(f"Final result: {len(validated_faces)} faces detected")
            return validated_faces
        
        return []
    
    def remove_duplicate_faces(self, face_locations: List[Tuple]) -> List[Tuple]:
        """Remove duplicate face detections that are too close to each other"""
        if len(face_locations) <= 1:
            return face_locations
        
        unique_faces = []
        for face in face_locations:
            top, right, bottom, left = face
            face_center = ((left + right) // 2, (top + bottom) // 2)
            face_size = max(right - left, bottom - top)
            
            is_duplicate = False
            for existing_face in unique_faces:
                ex_top, ex_right, ex_bottom, ex_left = existing_face
                ex_center = ((ex_left + ex_right) // 2, (ex_top + ex_bottom) // 2)
                
                # Calculate distance between face centers
                distance = ((face_center[0] - ex_center[0]) ** 2 + (face_center[1] - ex_center[1]) ** 2) ** 0.5
                min_size = min(face_size, max(ex_right - ex_left, ex_bottom - ex_top))
                
                # If faces are too close, consider them duplicates
                if distance < min_size * 0.5:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_faces.append(face)
        
        self.logger.debug(f"Removed {len(face_locations) - len(unique_faces)} duplicate faces")
        return unique_faces
    
    def filter_and_validate_faces(self, face_locations: List[Tuple]) -> List[Tuple]:
        """Filter out invalid faces and remove duplicates"""
        if not face_locations:
            return []
        
        # Filter by size and keep ALL valid faces (not just the largest)
        valid_faces = []
        
        for location in face_locations:
            top, right, bottom, left = location
            face_height = bottom - top
            face_width = right - left
            
            if face_height >= self.min_face_size and face_width >= self.min_face_size:
                valid_faces.append(location)
        
        # Sort by area (largest first) but keep all valid faces
        valid_faces.sort(key=lambda loc: (loc[2] - loc[0]) * (loc[1] - loc[3]), reverse=True)
        
        return valid_faces
    
    def fast_preprocess_image(self, image_path: str) -> np.ndarray:
        """Fast image preprocessing"""
        try:
            # Load image directly with OpenCV for speed
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Cannot load image: {image_path}")
            
            # Convert to RGB
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Resize if needed
            height, width = image.shape[:2]
            if width > self.max_image_width:
                scale_factor = self.max_image_width / width
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
            
            return image
            
        except Exception as e:
            self.logger.error(f"Error in fast preprocessing: {str(e)}")
            # Fallback to the enhanced method
            return self.enhance_image_quality(image_path)
    
    def get_student_images(self, student_folder: str) -> List[str]:
        """Get all image files for a student"""
        image_extensions = ['*.jpg', '*.jpeg', '*.png']
        image_paths = []
        
        if not os.path.exists(student_folder):
            return image_paths
        
        for extension in image_extensions:
            pattern = os.path.join(student_folder, extension)
            image_paths.extend(glob.glob(pattern))
        
        return sorted(list(set(image_paths)))
    
    def process_single_image(self, image_path: str):
        """Process a single image to extract face encoding"""
        try:
            if not os.path.exists(image_path):
                return None
                
            # Fast preprocessing
            image = self.fast_preprocess_image(image_path)
            
            # Fast face detection
            face_locations = self.fast_face_detection(image)
            
            if not face_locations:
                return None
            
            # Get encoding with minimal jitters
            face_encodings = face_recognition.face_encodings(
                image, 
                face_locations,
                num_jitters=1,  # Minimal jitters for speed
                model="small"    # Use smaller model
            )
            
            if face_encodings:
                return face_encodings[0]  # Return first encoding
            
        except Exception as e:
            self.logger.error(f"Error processing {image_path}: {str(e)}")
        
        return None
    
    def register_student(self, student_id: str, student_name: str, image_paths: List[str]) -> bool:
        """Register a student with optimized processing"""
        try:
            self.logger.info(f"Registering {student_name} ({student_id}) with {len(image_paths)} images")
            print(f"  Processing {student_name} ({student_id})...")
            
            all_encodings = []
            successful_images = 0
            
            # Process images in parallel
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all image processing tasks
                future_to_image = {
                    executor.submit(self.process_single_image, image_path): image_path 
                    for image_path in image_paths
                }
                
                # Process results as they complete
                for future in as_completed(future_to_image):
                    image_path = future_to_image[future]
                    try:
                        encoding = future.result()
                        if encoding is not None:
                            all_encodings.append(encoding)
                            successful_images += 1
                            self.logger.debug(f"Encoded face from {os.path.basename(image_path)}")
                    except Exception as e:
                        self.logger.error(f"Error processing {image_path}: {str(e)}")
            
            if not all_encodings:
                self.logger.error(f"No valid encodings for {student_name}")
                return False
            
            # Store student data
            student_data = {
                'name': student_name,
                'encodings': all_encodings,
                'registered_date': datetime.now().isoformat(),
                'image_count': successful_images,
                'total_encodings': len(all_encodings)
            }
            
            self.student_database[student_id] = student_data
            
            # Update known faces
            self.known_face_encodings.extend(all_encodings)
            self.known_face_names.extend([student_id] * len(all_encodings))
            
            # Save precomputed encoding for future use
            self.save_precomputed_encoding(student_id, student_data)
            
            self.logger.info(f"✓ {student_name}: {successful_images} images, {len(all_encodings)} encodings")
            return True
            
        except Exception as e:
            self.logger.error(f"Critical error registering {student_name}: {str(e)}")
            return False
    
    def batch_register_from_folders(self) -> Dict:
        """Batch register students from folder structure - optimized to use existing encodings"""
        self.logger.info("Starting optimized batch registration from folders...")
        
        if not os.path.exists(self.batch_images_path):
            return {
                'success': False,
                'message': f'Student photos directory not found: {self.batch_images_path}'
            }
        
        # Check if we already have proper name encodings
        encodings_path = os.path.join(self.models_path, "precomputed_encodings")
        existing_encodings = []
        if os.path.exists(encodings_path):
            encoding_files = glob.glob(os.path.join(encodings_path, "*.json"))
            # Only count proper name encodings (not STUDENT_xxx)
            existing_encodings = [f for f in encoding_files if not os.path.basename(f).startswith('STUDENT_')]
        
        # Find student folders
        student_folders = [f for f in os.listdir(self.batch_images_path) 
                          if os.path.isdir(os.path.join(self.batch_images_path, f))
                          and not f.startswith('.')]
        
        if not student_folders:
            return {
                'success': False,
                'message': 'No student folders found in student_photos directory'
            }
        
        results = {
            'total_students': len(student_folders),
            'successful': 0,
            'failed': 0,
            'details': {}
        }
        
        # If we have enough proper name encodings, use them instead of reprocessing
        if len(existing_encodings) >= len(student_folders):
            self.logger.info(f"Found {len(existing_encodings)} existing proper name encodings - using them instead of reprocessing")
            
            # Load from existing encodings
            for folder_name in student_folders:
                student_id = folder_name.upper()
                # Check if encoding exists for this student
                encoding_file = os.path.join(encodings_path, f"{student_id}.json")
                
                if os.path.exists(encoding_file):
                    results['successful'] += 1
                    results['details'][folder_name] = {
                        'success': True,
                        'student_id': student_id,
                        'student_name': folder_name.replace('_', ' ').title(),
                        'images': 'N/A (from existing encoding)',
                        'encodings': 'N/A (from existing encoding)',
                        'from_precomputed': True
                    }
                else:
                    results['failed'] += 1
                    results['details'][folder_name] = {
                        'success': False,
                        'message': 'No existing encoding found',
                        'images': 0
                    }
            
            return results
        
        # Otherwise, process only missing students
        students_to_process = []
        for folder_name in student_folders:
            student_id = folder_name.upper()
            encoding_file = os.path.join(encodings_path, f"{student_id}.json")
            
            if os.path.exists(encoding_file):
                # Already have encoding for this student
                results['successful'] += 1
                results['details'][folder_name] = {
                    'success': True,
                    'student_id': student_id,
                    'student_name': folder_name.replace('_', ' ').title(),
                    'images': 'N/A (from existing encoding)',
                    'encodings': 'N/A (from existing encoding)',
                    'from_precomputed': True
                }
            else:
                students_to_process.append(folder_name)
        
        # Process only students not already in database
        for folder_name in students_to_process:
            student_folder = os.path.join(self.batch_images_path, folder_name)
            image_paths = self.get_student_images(student_folder)
            
            if not image_paths:
                self.logger.warning(f"No images found in {folder_name}")
                results['failed'] += 1
                results['details'][folder_name] = {
                    'success': False,
                    'message': 'No images found',
                    'images': 0
                }
                continue
            
            # Generate student info from folder name
            student_id = folder_name.upper()
            student_name = folder_name.replace('_', ' ').title()
            
            success = self.register_student(student_id, student_name, image_paths)
            
            if success:
                results['successful'] += 1
                results['details'][folder_name] = {
                    'success': True,
                    'student_id': student_id,
                    'student_name': student_name,
                    'images': len(image_paths),
                    'encodings': len(self.student_database[student_id]['encodings']),
                    'from_precomputed': False
                }
            else:
                results['failed'] += 1
                results['details'][folder_name] = {
                    'success': False,
                    'message': 'Registration failed',
                    'images': len(image_paths)
                }
        
        # Save database
        self.save_student_database()
        
        return results
    
    # The rest of the methods (recognize_faces, process_attendance_image, etc.)
    # remain similar to the previous implementation but can be optimized similarly
    
    def save_student_database(self):
        """Save student database"""
        try:
            db_path = os.path.join(self.models_path, "student_database.pkl")
            data = {
                'student_database': self.student_database,
                'known_face_encodings': self.known_face_encodings,
                'known_face_names': self.known_face_names,
                'last_updated': datetime.now().isoformat(),
                'total_students': len(self.student_database)
            }
            
            with open(db_path, 'wb') as f:
                pickle.dump(data, f)
            
            self.logger.info(f"Database saved: {len(self.student_database)} students")
            
        except Exception as e:
            self.logger.error(f"Error saving database: {str(e)}")
    
    def load_student_database(self):
        """Load student database - prioritize proper name encodings only"""
        try:
            # Clear any existing data first
            self.student_database = {}
            self.known_face_encodings = []
            self.known_face_names = []
            
            # ONLY load from precomputed encodings with proper names
            success = self.load_precomputed_encodings()
            
            if not success:
                self.logger.warning("No precomputed encodings found with proper names")
                # Try to register from folders if no encodings exist
                self.logger.info("Attempting to register students from folders...")
                self.batch_register_from_folders()
            
        except Exception as e:
            self.logger.error(f"Error loading database: {str(e)}")
            self.student_database = {}
            self.known_face_encodings = []
            self.known_face_names = []

# Main functions remain similar but use the optimized system
def register_all_students():
    """Register all students from folder structure"""
    print("=== Optimized Batch Student Registration ===")
    
    system = OptimizedAttendanceSystem()
    
    # Verify setup first
    print("Verifying system setup...")
    system.verify_system_setup()
    
    # Check if student folders exist with images
    if not os.path.exists(system.batch_images_path):
        print(f"❌ Student photos directory not found: {system.batch_images_path}")
        print("Please run setup first and add student photos.")
        return
    
    student_folders = [f for f in os.listdir(system.batch_images_path) 
                      if os.path.isdir(os.path.join(system.batch_images_path, f))
                      and not f.startswith('.')]
    
    if not student_folders:
        print("❌ No student folders found!")
        print("Please create folders like student_001, student_002, etc. in student_photos directory")
        return
    
    print(f"Found {len(student_folders)} student folders")
    
    # Check if we can use precomputed encodings
    encodings_path = os.path.join(system.models_path, "precomputed_encodings")
    if os.path.exists(encodings_path):
        encoding_files = glob.glob(os.path.join(encodings_path, "*.json"))
        if encoding_files:
            print(f"Found {len(encoding_files)} precomputed encodings - will use for faster processing")
    
    # Proceed with registration
    print(f"\nStarting registration for {len(student_folders)} students...")
    start_time = time.time()
    results = system.batch_register_from_folders()
    end_time = time.time()
    
    print(f"\n=== Registration Results ===")
    print(f"Total processing time: {end_time - start_time:.2f} seconds")
    print(f"Total students processed: {results['total_students']}")
    print(f"Successful registrations: {results['successful']}")
    print(f"Failed registrations: {results['failed']}")
    print(f"Success rate: {results['successful']}/{results['total_students']} ({results['successful']/results['total_students']*100:.1f}%)")
    
    print(f"\nDetailed Results:")
    for folder, details in results['details'].items():
        if details['success']:
            source = "precomputed" if details.get('from_precomputed', False) else "new"
            print(f"✓ {folder}: {details['student_name']} - {details['encodings']} encodings ({source})")
        else:
            print(f"❌ {folder}: {details['message']} ({details['images']} images)")
    
    return system

# Other main functions (setup_directories, process_classroom_images, etc.)
# would be similar to the previous implementation but use OptimizedAttendanceSystem

def main():
    """Main function with optimized options"""
    print("Optimized Smart Attendance System")
    print("=" * 50)
    print("Your system path: C:/Users/atifk/Desktop/Attendence/attendance_project")
    
    try:
        choice = input("""
Choose an option:
1. Setup Directory Structure (Run this first)
2. Register All Students (Fast batch registration)
3. Process Classroom Images (Mark attendance)
4. Test with Single Image (Quick test)
5. Verify System Setup (Check current status)

Enter choice (1-5): """)
        
        if choice == "1":
            # setup_directories() would need to be implemented
            print("Setup functionality would be implemented here")
        
        elif choice == "2":
            register_all_students()
        
        elif choice == "3":
            # process_classroom_images() would need to be implemented
            print("Process classroom images functionality would be implemented here")
        
        elif choice == "4":
            # test_with_single_image() would need to be implemented
            print("Test with single image functionality would be implemented here")
        
        elif choice == "5":
            system = OptimizedAttendanceSystem()
            system.verify_system_setup()
        
        else:
            print("Invalid choice. Please select 1-5.")
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print("Please check your setup and try again.")

if __name__ == "__main__":
    main()