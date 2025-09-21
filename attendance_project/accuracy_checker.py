import cv2
import numpy as np
import face_recognition
import os
import json
import pandas as pd
from datetime import datetime, date
import glob
from typing import List, Dict, Tuple
import pickle

# Optional imports - will work without matplotlib/seaborn
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False
    print("Note: matplotlib/seaborn not available. Visualizations will be skipped.")

class FixedAttendanceAccuracyChecker:
    """
    Fixed Tool to check and analyze attendance system accuracy
    """
    
    def __init__(self, base_path: str = "C:/Users/atifk/Desktop/Attendence/attendance_project"):
        self.base_path = base_path
        self.attendance_path = os.path.join(base_path, "attendance_records")
        self.models_path = os.path.join(base_path, "models")
        self.classroom_images_path = os.path.join(base_path, "classroom_photos")
        
        # Verify paths exist
        self.verify_paths()
    
    def verify_paths(self):
        """Verify that required paths exist"""
        required_paths = [self.base_path, self.attendance_path, self.models_path]
        
        for path in required_paths:
            if not os.path.exists(path):
                print(f"Warning: Path does not exist: {path}")
                try:
                    os.makedirs(path, exist_ok=True)
                    print(f"Created directory: {path}")
                except Exception as e:
                    print(f"Could not create directory {path}: {e}")
    
    def check_system_status(self):
        """Check basic system status"""
        print("=== System Status Check ===")
        
        # Check base directory
        print(f"Base directory: {self.base_path}")
        print(f"Base directory exists: {os.path.exists(self.base_path)}")
        
        # Check for registered students
        student_count = 0
        db_path = os.path.join(self.models_path, "student_database.pkl")
        if os.path.exists(db_path):
            try:
                with open(db_path, 'rb') as f:
                    data = pickle.load(f)
                student_count = len(data.get('student_database', {}))
            except Exception as e:
                print(f"Error loading student database: {e}")
        
        print(f"Registered students: {student_count}")
        
        # Check attendance records
        attendance_files = glob.glob(os.path.join(self.attendance_path, "attendance_*.json"))
        print(f"Attendance record files: {len(attendance_files)}")
        
        # Check annotated images
        annotated_files = glob.glob(os.path.join(self.attendance_path, "annotated_*.jpg"))
        print(f"Annotated images: {len(annotated_files)}")
        
        # Check classroom images
        if os.path.exists(self.classroom_images_path):
            classroom_images = []
            for ext in ['*.jpg', '*.jpeg', '*.png', '*.bmp']:
                classroom_images.extend(glob.glob(os.path.join(self.classroom_images_path, ext)))
            print(f"Classroom images available: {len(classroom_images)}")
        else:
            print("Classroom images directory not found")
        
        return student_count, len(attendance_files), len(annotated_files)
    
    def check_detection_accuracy(self, ground_truth_file: str = None) -> Dict:
        """
        Check face detection accuracy with proper error handling
        """
        print("=== Face Detection Accuracy Check ===")
        
        # Initialize results
        accuracy_results = {
            'total_images_processed': 0,
            'total_faces_detected': 0,
            'total_students_recognized': 0,
            'images_with_no_faces': 0,
            'detection_rate_per_image': [],
            'recognition_accuracy': [],
            'detailed_results': []
        }
        
        # Load ground truth if provided
        ground_truth = {}
        if ground_truth_file and os.path.exists(ground_truth_file):
            try:
                gt_df = pd.read_csv(ground_truth_file)
                for _, row in gt_df.iterrows():
                    image_name = row['image_name']
                    if image_name not in ground_truth:
                        ground_truth[image_name] = []
                    if row.get('present', 0) == 1:
                        ground_truth[image_name].append(str(row['student_id']))
                print(f"Loaded ground truth data for {len(ground_truth)} images")
            except Exception as e:
                print(f"Error loading ground truth file: {e}")
                ground_truth = {}
        
        # Find all attendance records
        attendance_files = glob.glob(os.path.join(self.attendance_path, "attendance_*.json"))
        
        if not attendance_files:
            print("No attendance record files found!")
            print(f"Expected location: {self.attendance_path}")
            print("Make sure you have processed some classroom images first.")
            return accuracy_results
        
        print(f"Found {len(attendance_files)} attendance record files")
        
        # Process each attendance file
        for attendance_file in attendance_files:
            try:
                with open(attendance_file, 'r', encoding='utf-8') as f:
                    daily_records = json.load(f)
                
                print(f"Processing {len(daily_records)} records from {os.path.basename(attendance_file)}")
                
                for record in daily_records:
                    accuracy_results['total_images_processed'] += 1
                    
                    image_name = os.path.basename(record.get('image_path', 'unknown'))
                    faces_detected = record.get('total_faces_detected', 0)
                    students_recognized = record.get('recognized_students', 0)
                    unknown_faces = record.get('unknown_faces', 0)
                    
                    accuracy_results['total_faces_detected'] += faces_detected
                    accuracy_results['total_students_recognized'] += students_recognized
                    
                    if faces_detected == 0:
                        accuracy_results['images_with_no_faces'] += 1
                    
                    # Calculate detection rate for this image
                    detection_rate = (students_recognized / max(faces_detected, 1)) * 100
                    accuracy_results['detection_rate_per_image'].append(detection_rate)
                    
                    # Compare with ground truth if available
                    if image_name in ground_truth:
                        actual_students = set(ground_truth[image_name])
                        detected_students = set([str(s.get('student_id', '')) for s in record.get('present_students', [])])
                        
                        true_positives = len(actual_students & detected_students)
                        false_positives = len(detected_students - actual_students)
                        false_negatives = len(actual_students - detected_students)
                        
                        precision = true_positives / max(len(detected_students), 1)
                        recall = true_positives / max(len(actual_students), 1)
                        f1_score = 2 * (precision * recall) / max((precision + recall), 0.001)
                        
                        accuracy_results['recognition_accuracy'].append({
                            'image': image_name,
                            'precision': precision,
                            'recall': recall,
                            'f1_score': f1_score,
                            'true_positives': true_positives,
                            'false_positives': false_positives,
                            'false_negatives': false_negatives
                        })
                    
                    # Store detailed results
                    accuracy_results['detailed_results'].append({
                        'image': image_name,
                        'faces_detected': faces_detected,
                        'students_recognized': students_recognized,
                        'unknown_faces': unknown_faces,
                        'recognition_rate': detection_rate,
                        'timestamp': record.get('timestamp', 'unknown')
                    })
                    
            except Exception as e:
                print(f"Error processing {attendance_file}: {e}")
                continue
        
        # Calculate overall statistics
        if accuracy_results['total_images_processed'] > 0:
            accuracy_results['avg_faces_per_image'] = accuracy_results['total_faces_detected'] / accuracy_results['total_images_processed']
            accuracy_results['avg_recognition_rate'] = np.mean(accuracy_results['detection_rate_per_image']) if accuracy_results['detection_rate_per_image'] else 0
            accuracy_results['images_with_faces'] = accuracy_results['total_images_processed'] - accuracy_results['images_with_no_faces']
            accuracy_results['face_detection_success_rate'] = (accuracy_results['images_with_faces'] / accuracy_results['total_images_processed']) * 100
        
        if accuracy_results['recognition_accuracy']:
            avg_precision = np.mean([r['precision'] for r in accuracy_results['recognition_accuracy']])
            avg_recall = np.mean([r['recall'] for r in accuracy_results['recognition_accuracy']])
            avg_f1 = np.mean([r['f1_score'] for r in accuracy_results['recognition_accuracy']])
            
            accuracy_results['overall_precision'] = avg_precision
            accuracy_results['overall_recall'] = avg_recall
            accuracy_results['overall_f1_score'] = avg_f1
        
        return accuracy_results
    
    def print_accuracy_report(self, results: Dict):
        """Print formatted accuracy report with error handling"""
        print(f"\n{'='*60}")
        print("ATTENDANCE SYSTEM ACCURACY REPORT")
        print(f"{'='*60}")
        
        if results['total_images_processed'] == 0:
            print("No processed images found!")
            print("\nPossible issues:")
            print("1. No attendance records exist yet")
            print("2. Attendance records are in wrong location")
            print("3. JSON files are corrupted")
            print("\nPlease process some classroom images first using your main system.")
            return
        
        print(f"Total Images Processed: {results['total_images_processed']}")
        print(f"Total Faces Detected: {results['total_faces_detected']}")
        print(f"Total Students Recognized: {results['total_students_recognized']}")
        
        print(f"\nFace Detection Performance:")
        print(f"  Images with faces detected: {results['images_with_faces']}/{results['total_images_processed']}")
        print(f"  Face detection success rate: {results['face_detection_success_rate']:.1f}%")
        print(f"  Average faces per image: {results['avg_faces_per_image']:.1f}")
        print(f"  Average recognition rate: {results['avg_recognition_rate']:.1f}%")
        
        if 'overall_precision' in results:
            print(f"\nRecognition Accuracy (vs Ground Truth):")
            print(f"  Precision: {results['overall_precision']:.3f}")
            print(f"  Recall: {results['overall_recall']:.3f}")
            print(f"  F1-Score: {results['overall_f1_score']:.3f}")
        
        # Show best performing images
        if results['detailed_results']:
            print(f"\nTop Performing Images:")
            sorted_results = sorted(results['detailed_results'], 
                                   key=lambda x: x['recognition_rate'], reverse=True)[:5]
            
            for i, result in enumerate(sorted_results, 1):
                print(f"  {i}. {result['image']}: {result['recognition_rate']:.1f}% "
                      f"({result['students_recognized']}/{result['faces_detected']} faces)")
            
            # Show problematic images
            print(f"\nImages with Detection Issues:")
            problem_images = [r for r in results['detailed_results'] if r['faces_detected'] == 0]
            if problem_images:
                for result in problem_images[:5]:
                    print(f"  ❌ {result['image']}: No faces detected")
            else:
                print("  ✓ No major detection issues found")
    
    def create_accuracy_visualizations(self, results: Dict, save_path: str = None):
        """Create visualizations with error handling"""
        if not PLOTTING_AVAILABLE:
            print("Matplotlib not available. Cannot create visualizations.")
            print("Install with: pip install matplotlib seaborn")
            return
        
        if not results['detailed_results']:
            print("No data available for visualization")
            return
        
        try:
            # Create subplot figure
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            fig.suptitle('Attendance System Accuracy Analysis', fontsize=16)
            
            # 1. Recognition Rate Distribution
            recognition_rates = [r['recognition_rate'] for r in results['detailed_results']]
            axes[0, 0].hist(recognition_rates, bins=min(20, len(recognition_rates)), 
                           alpha=0.7, color='skyblue', edgecolor='black')
            axes[0, 0].set_title('Distribution of Recognition Rates')
            axes[0, 0].set_xlabel('Recognition Rate (%)')
            axes[0, 0].set_ylabel('Number of Images')
            axes[0, 0].axvline(np.mean(recognition_rates), color='red', linestyle='--', 
                              label=f'Average: {np.mean(recognition_rates):.1f}%')
            axes[0, 0].legend()
            
            # 2. Faces Detected vs Students Recognized
            faces_detected = [r['faces_detected'] for r in results['detailed_results']]
            students_recognized = [r['students_recognized'] for r in results['detailed_results']]
            
            axes[0, 1].scatter(faces_detected, students_recognized, alpha=0.6, color='green')
            max_faces = max(faces_detected) if faces_detected else 1
            axes[0, 1].plot([0, max_faces], [0, max_faces], 'r--', label='Perfect Recognition')
            axes[0, 1].set_title('Faces Detected vs Students Recognized')
            axes[0, 1].set_xlabel('Faces Detected')
            axes[0, 1].set_ylabel('Students Recognized')
            axes[0, 1].legend()
            
            # 3. Unknown Faces Analysis
            unknown_faces = [r['unknown_faces'] for r in results['detailed_results']]
            images_with_unknown = sum(1 for u in unknown_faces if u > 0)
            
            axes[1, 0].bar(['With Unknown', 'Total Images'], 
                          [images_with_unknown, len(unknown_faces)], 
                          color=['orange', 'lightblue'], alpha=0.7)
            axes[1, 0].set_title('Images with Unknown Faces')
            axes[1, 0].set_ylabel('Number of Images')
            
            # 4. Performance Summary
            axes[1, 1].text(0.1, 0.8, f"Total Images: {results['total_images_processed']}", 
                           transform=axes[1, 1].transAxes, fontsize=12)
            axes[1, 1].text(0.1, 0.7, f"Faces Detected: {results['total_faces_detected']}", 
                           transform=axes[1, 1].transAxes, fontsize=12)
            axes[1, 1].text(0.1, 0.6, f"Students Recognized: {results['total_students_recognized']}", 
                           transform=axes[1, 1].transAxes, fontsize=12)
            axes[1, 1].text(0.1, 0.5, f"Success Rate: {results['face_detection_success_rate']:.1f}%", 
                           transform=axes[1, 1].transAxes, fontsize=12)
            axes[1, 1].set_title('Summary Statistics')
            axes[1, 1].set_xlim(0, 1)
            axes[1, 1].set_ylim(0, 1)
            axes[1, 1].axis('off')
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                print(f"Visualization saved to: {save_path}")
            else:
                plt.show()
                
        except Exception as e:
            print(f"Error creating visualizations: {e}")
    
    def export_detailed_results(self, results: Dict, export_path: str = None):
        """Export detailed results to CSV with error handling"""
        if not results['detailed_results']:
            print("No data to export")
            return
        
        try:
            if export_path is None:
                export_path = os.path.join(self.attendance_path, f"accuracy_report_{date.today()}.csv")
            
            # Convert to DataFrame
            df = pd.DataFrame(results['detailed_results'])
            df.to_csv(export_path, index=False)
            
            # Create summary file
            summary_data = {
                'Metric': ['Total Images', 'Total Faces Detected', 'Total Students Recognized',
                          'Average Recognition Rate', 'Face Detection Success Rate'],
                'Value': [results['total_images_processed'], results['total_faces_detected'],
                         results['total_students_recognized'], 
                         f"{results.get('avg_recognition_rate', 0):.1f}%",
                         f"{results.get('face_detection_success_rate', 0):.1f}%"]
            }
            
            summary_df = pd.DataFrame(summary_data)
            summary_path = export_path.replace('.csv', '_summary.csv')
            summary_df.to_csv(summary_path, index=False)
            
            print(f"Detailed results exported to: {export_path}")
            print(f"Summary exported to: {summary_path}")
            
        except Exception as e:
            print(f"Error exporting results: {e}")
    
    def test_single_image_accuracy(self, image_path: str = None):
        """Test accuracy on a single image"""
        if image_path is None:
            # Try to find a classroom image automatically
            if os.path.exists(self.classroom_images_path):
                image_files = []
                for ext in ['*.jpg', '*.jpeg', '*.png']:
                    image_files.extend(glob.glob(os.path.join(self.classroom_images_path, ext)))
                
                if image_files:
                    image_path = image_files[0]
                    print(f"Using first available image: {os.path.basename(image_path)}")
                else:
                    print("No classroom images found for testing")
                    return
            else:
                print("Classroom images directory not found")
                return
        
        print(f"=== Testing Single Image: {os.path.basename(image_path)} ===")
        
        if not os.path.exists(image_path):
            print(f"❌ Image not found: {image_path}")
            return
        
        try:
            # Load image and detect faces manually
            image = cv2.imread(image_path)
            if image is None:
                print(f"❌ Could not load image: {image_path}")
                return
                
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Test different detection methods
            detection_methods = [
                ("HOG", lambda: face_recognition.face_locations(rgb_image, model="hog")),
                ("HOG+Upsample", lambda: face_recognition.face_locations(rgb_image, 1, "hog")),
            ]
            
            print("Face Detection Results:")
            for method_name, method_func in detection_methods:
                try:
                    faces = method_func()
                    print(f"  {method_name}: {len(faces)} faces detected")
                    
                    if faces:
                        for i, (top, right, bottom, left) in enumerate(faces):
                            width = right - left
                            height = bottom - top
                            print(f"    Face {i+1}: {width}x{height} pixels at ({left}, {top})")
                except Exception as e:
                    print(f"  {method_name}: Failed - {str(e)}")
            
            # Check if this image has been processed by the system
            self.check_system_processing_for_image(image_path)
            
        except Exception as e:
            print(f"Error testing image: {e}")
    
    def check_system_processing_for_image(self, image_path: str):
        """Check if image has been processed by the system"""
        attendance_files = glob.glob(os.path.join(self.attendance_path, "attendance_*.json"))
        image_name = os.path.basename(image_path)
        
        system_results = None
        for attendance_file in attendance_files:
            try:
                with open(attendance_file, 'r', encoding='utf-8') as f:
                    daily_records = json.load(f)
                
                for record in daily_records:
                    if os.path.basename(record.get('image_path', '')) == image_name:
                        system_results = record
                        break
                
                if system_results:
                    break
                    
            except Exception as e:
                print(f"Error reading {attendance_file}: {e}")
                continue
        
        if system_results:
            print(f"\nSystem Processing Results:")
            print(f"  Faces detected: {system_results.get('total_faces_detected', 0)}")
            print(f"  Students recognized: {system_results.get('recognized_students', 0)}")
            print(f"  Unknown faces: {system_results.get('unknown_faces', 0)}")
            
            present_students = system_results.get('present_students', [])
            if present_students:
                print(f"  Recognized students:")
                for student in present_students:
                    print(f"    - {student.get('student_name', 'Unknown')} ({student.get('student_id', 'Unknown')})")
            else:
                print("  No students recognized")
        else:
            print(f"\n⚠ This image has not been processed by the system yet")
            print("Run your main attendance system to process this image first.")


def create_ground_truth_template():
    """Create a template CSV file for ground truth data"""
    template_path = "ground_truth_template.csv"
    
    sample_data = {
        'image_name': ['classroom_photo_1.jpg', 'classroom_photo_1.jpg', 'classroom_photo_2.jpg'],
        'student_id': ['STUDENT_001', 'STUDENT_002', 'STUDENT_003'], 
        'present': [1, 1, 0]  # 1 for present, 0 for absent
    }
    
    try:
        df = pd.DataFrame(sample_data)
        df.to_csv(template_path, index=False)
        print(f"Ground truth template created: {template_path}")
        print("Fill this template with actual attendance data for accuracy checking")
    except Exception as e:
        print(f"Error creating template: {e}")


def main_accuracy_check():
    """Main function for accuracy checking with improved error handling"""
    print("Attendance System Accuracy Checker")
    print("=" * 50)
    
    try:
        checker = FixedAttendanceAccuracyChecker()
        
        # First, show system status
        print("\nSystem Status:")
        students, records, images = checker.check_system_status()
        
        if students == 0:
            print("\n⚠ WARNING: No students registered!")
            print("Please register students first using your main system.")
        
        if records == 0:
            print("\n⚠ WARNING: No attendance records found!")
            print("Please process some classroom images first using your main system.")
            print("The accuracy checker needs attendance data to analyze.")
            return
        
        choice = input("""
Choose an option:
1. Check Overall System Accuracy
2. Test Single Image
3. Create Ground Truth Template
4. Export Detailed Results
5. Create Accuracy Visualizations

Enter choice (1-5): """)
        
        if choice == "1":
            ground_truth_file = input("Enter path to ground truth CSV (optional, press Enter to skip): ").strip()
            if not ground_truth_file:
                ground_truth_file = None
            
            print("\nAnalyzing attendance records...")
            results = checker.check_detection_accuracy(ground_truth_file)
            checker.print_accuracy_report(results)
            
            # Ask if user wants to save results
            save_choice = input("\nSave detailed results to CSV? (y/n): ").lower()
            if save_choice == 'y':
                checker.export_detailed_results(results)
        
        elif choice == "2":
            image_path = input("Enter path to test image (or press Enter to use first available): ").strip()
            if not image_path:
                image_path = None
            checker.test_single_image_accuracy(image_path)
        
        elif choice == "3":
            create_ground_truth_template()
        
        elif choice == "4":
            print("Generating detailed results...")
            results = checker.check_detection_accuracy()
            export_path = input("Enter export path (or press Enter for default): ").strip()
            checker.export_detailed_results(results, export_path if export_path else None)
        
        elif choice == "5":
            if not PLOTTING_AVAILABLE:
                print("Plotting libraries not available. Install with: pip install matplotlib seaborn")
                return
                
            print("Creating accuracy visualizations...")
            results = checker.check_detection_accuracy()
            save_path = input("Enter path to save visualization (or press Enter for display): ").strip()
            checker.create_accuracy_visualizations(results, save_path if save_path else None)
        
        else:
            print("Invalid choice. Please select 1-5.")
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        print("Please check your system setup and try again.")

if __name__ == "__main__":
    main_accuracy_check()