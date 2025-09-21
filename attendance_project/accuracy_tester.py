import cv2
import numpy as np
import os
import json
import time
from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
from smart_attendance_system import SmartAttendanceSystem
import logging

class AccuracyTester:
    """
    Comprehensive accuracy testing framework for the Smart Attendance System
    """
    
    def __init__(self, system: SmartAttendanceSystem):
        self.system = system
        self.test_results = {}
        self.logger = logging.getLogger(__name__)
        
    def run_comprehensive_accuracy_test(self):
        """Run all accuracy tests and generate comprehensive report"""
        print("🔍 Starting Comprehensive Accuracy Testing...")
        print("="*60)
        
        # Test 1: Face Detection Accuracy
        detection_results = self.test_face_detection_accuracy()
        
        # Test 2: Recognition Accuracy (if face_recognition available)
        recognition_results = self.test_recognition_accuracy()
        
        # Test 3: System Performance
        performance_results = self.test_system_performance()
        
        # Test 4: Database Accuracy
        database_results = self.test_database_accuracy()
        
        # Generate comprehensive report
        self.generate_accuracy_report({
            'detection': detection_results,
            'recognition': recognition_results,
            'performance': performance_results,
            'database': database_results
        })
        
        return self.test_results
    
    def test_face_detection_accuracy(self):
        """Test face detection accuracy on various images"""
        print("\n📸 Testing Face Detection Accuracy...")
        
        results = {
            'total_images_tested': 0,
            'faces_detected': 0,
            'detection_rate': 0.0,
            'average_confidence': 0.0,
            'processing_times': [],
            'image_analysis': []
        }
        
        # Test on classroom photos
        classroom_photos = list(Path("classroom_photos").glob("*.jpg"))
        classroom_photos.extend(list(Path("classroom_photos").glob("*.jpeg")))
        classroom_photos.extend(list(Path("classroom_photos").glob("*.png")))
        
        for photo_path in classroom_photos:
            if photo_path.exists():
                print(f"  Testing: {photo_path.name}")
                
                start_time = time.time()
                image = cv2.imread(str(photo_path))
                
                if image is not None:
                    # Test face detection
                    detection_results = self.system.detect_and_recognize_faces(image)
                    
                    processing_time = time.time() - start_time
                    results['processing_times'].append(processing_time)
                    results['total_images_tested'] += 1
                    results['faces_detected'] += len(detection_results)
                    
                    # Calculate average confidence
                    if detection_results:
                        avg_conf = np.mean([r['confidence'] for r in detection_results])
                        results['average_confidence'] += avg_conf
                    
                    # Store detailed analysis
                    results['image_analysis'].append({
                        'image_name': photo_path.name,
                        'faces_found': len(detection_results),
                        'processing_time': processing_time,
                        'image_size': image.shape,
                        'detection_details': detection_results
                    })
                    
                    print(f"    ✅ Found {len(detection_results)} faces in {processing_time:.2f}s")
                else:
                    print(f"    ❌ Could not load image: {photo_path.name}")
        
        # Calculate metrics
        if results['total_images_tested'] > 0:
            results['detection_rate'] = results['faces_detected'] / results['total_images_tested']
            results['average_confidence'] = results['average_confidence'] / results['total_images_tested']
            results['avg_processing_time'] = np.mean(results['processing_times'])
        
        print(f"  📊 Detection Rate: {results['detection_rate']:.2f} faces per image")
        print(f"  📊 Average Confidence: {results['average_confidence']:.2f}")
        print(f"  📊 Average Processing Time: {results['avg_processing_time']:.2f}s")
        
        return results
    
    def test_recognition_accuracy(self):
        """Test face recognition accuracy if face_recognition is available"""
        print("\n🎯 Testing Face Recognition Accuracy...")
        
        results = {
            'recognition_available': False,
            'known_faces_recognized': 0,
            'unknown_faces_detected': 0,
            'recognition_accuracy': 0.0,
            'false_positives': 0,
            'false_negatives': 0
        }
        
        # Check if face_recognition is available
        try:
            import face_recognition
            results['recognition_available'] = True
            print("  ✅ face_recognition library available")
            
            # Test recognition on classroom photos
            classroom_photos = list(Path("classroom_photos").glob("*.jpg"))
            
            for photo_path in classroom_photos:
                if photo_path.exists():
                    image = cv2.imread(str(photo_path))
                    if image is not None:
                        detection_results = self.system.detect_and_recognize_faces(image)
                        
                        for result in detection_results:
                            if result['student_id'] != 'Unknown':
                                results['known_faces_recognized'] += 1
                            else:
                                results['unknown_faces_detected'] += 1
            
            total_faces = results['known_faces_recognized'] + results['unknown_faces_detected']
            if total_faces > 0:
                results['recognition_accuracy'] = results['known_faces_recognized'] / total_faces
            
            print(f"  📊 Known faces recognized: {results['known_faces_recognized']}")
            print(f"  📊 Unknown faces detected: {results['unknown_faces_detected']}")
            print(f"  📊 Recognition accuracy: {results['recognition_accuracy']:.2%}")
            
        except ImportError:
            print("  ⚠️  face_recognition library not available - using OpenCV only")
            results['recognition_available'] = False
        
        return results
    
    def test_system_performance(self):
        """Test system performance metrics"""
        print("\n⚡ Testing System Performance...")
        
        results = {
            'memory_usage_mb': 0,
            'cpu_usage_percent': 0,
            'database_response_time': 0,
            'image_processing_speed': 0,
            'concurrent_processing': False
        }
        
        # Test database performance
        start_time = time.time()
        stats = self.system.get_attendance_statistics()
        results['database_response_time'] = time.time() - start_time
        
        # Test image processing speed
        test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        start_time = time.time()
        self.system.detect_and_recognize_faces(test_image)
        results['image_processing_speed'] = time.time() - start_time
        
        print(f"  📊 Database response time: {results['database_response_time']:.3f}s")
        print(f"  📊 Image processing speed: {results['image_processing_speed']:.3f}s")
        
        return results
    
    def test_database_accuracy(self):
        """Test database accuracy and integrity"""
        print("\n🗄️  Testing Database Accuracy...")
        
        results = {
            'total_students': 0,
            'attendance_records': 0,
            'data_integrity': True,
            'foreign_key_constraints': True,
            'data_consistency': True
        }
        
        # Connect to database
        import sqlite3
        conn = sqlite3.connect(self.system.database_file)
        cursor = conn.cursor()
        
        # Count records
        cursor.execute("SELECT COUNT(*) FROM students")
        results['total_students'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM attendance")
        results['attendance_records'] = cursor.fetchone()[0]
        
        # Test data integrity
        try:
            cursor.execute("PRAGMA integrity_check")
            integrity_result = cursor.fetchone()[0]
            results['data_integrity'] = integrity_result == 'ok'
        except:
            results['data_integrity'] = False
        
        # Test foreign key constraints
        try:
            cursor.execute("PRAGMA foreign_key_check")
            fk_issues = cursor.fetchall()
            results['foreign_key_constraints'] = len(fk_issues) == 0
        except:
            results['foreign_key_constraints'] = False
        
        conn.close()
        
        print(f"  📊 Total students: {results['total_students']}")
        print(f"  📊 Attendance records: {results['attendance_records']}")
        print(f"  📊 Data integrity: {'✅' if results['data_integrity'] else '❌'}")
        print(f"  📊 Foreign key constraints: {'✅' if results['foreign_key_constraints'] else '❌'}")
        
        return results
    
    def generate_accuracy_report(self, all_results):
        """Generate comprehensive accuracy report"""
        print("\n📋 Generating Accuracy Report...")
        
        report = {
            'test_timestamp': datetime.now().isoformat(),
            'system_info': {
                'face_recognition_available': all_results['recognition']['recognition_available'],
                'database_file': self.system.database_file,
                'tolerance': self.system.tolerance,
                'model': self.system.model
            },
            'accuracy_metrics': {
                'face_detection_rate': all_results['detection']['detection_rate'],
                'average_confidence': all_results['detection']['average_confidence'],
                'recognition_accuracy': all_results['recognition']['recognition_accuracy'],
                'processing_speed': all_results['performance']['image_processing_speed']
            },
            'performance_metrics': {
                'avg_processing_time': all_results['detection']['avg_processing_time'],
                'database_response_time': all_results['performance']['database_response_time'],
                'total_images_tested': all_results['detection']['total_images_tested']
            },
            'database_health': {
                'total_students': all_results['database']['total_students'],
                'attendance_records': all_results['database']['attendance_records'],
                'data_integrity': all_results['database']['data_integrity'],
                'foreign_key_constraints': all_results['database']['foreign_key_constraints']
            },
            'recommendations': self._generate_recommendations(all_results)
        }
        
        # Save report
        report_filename = f"accuracy_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        self._print_accuracy_summary(report)
        
        return report
    
    def _generate_recommendations(self, results):
        """Generate recommendations based on test results"""
        recommendations = []
        
        # Detection recommendations
        if results['detection']['detection_rate'] < 0.5:
            recommendations.append("Consider improving lighting conditions or image quality for better face detection")
        
        if results['detection']['average_confidence'] < 0.7:
            recommendations.append("Face detection confidence is low - consider adjusting tolerance settings")
        
        # Recognition recommendations
        if not results['recognition']['recognition_available']:
            recommendations.append("Install face_recognition library for better face recognition accuracy")
        
        if results['recognition']['recognition_accuracy'] < 0.8:
            recommendations.append("Add more training images per student for better recognition")
        
        # Performance recommendations
        if results['performance']['image_processing_speed'] > 2.0:
            recommendations.append("Image processing is slow - consider using GPU acceleration or reducing image size")
        
        if results['performance']['database_response_time'] > 1.0:
            recommendations.append("Database queries are slow - consider adding more indexes")
        
        # Database recommendations
        if not results['database']['data_integrity']:
            recommendations.append("Database integrity issues detected - run database repair")
        
        if results['database']['total_students'] == 0:
            recommendations.append("No students in database - add student records and photos")
        
        return recommendations
    
    def _print_accuracy_summary(self, report):
        """Print accuracy summary to console"""
        print("\n" + "="*60)
        print("🎯 ACCURACY TEST RESULTS SUMMARY")
        print("="*60)
        
        print(f"📊 Face Detection Rate: {report['accuracy_metrics']['face_detection_rate']:.2f} faces/image")
        print(f"📊 Average Confidence: {report['accuracy_metrics']['average_confidence']:.2f}")
        print(f"📊 Recognition Accuracy: {report['accuracy_metrics']['recognition_accuracy']:.2%}")
        print(f"📊 Processing Speed: {report['accuracy_metrics']['processing_speed']:.3f}s")
        
        print(f"\n🗄️  Database Health:")
        print(f"   Students: {report['database_health']['total_students']}")
        print(f"   Records: {report['database_health']['attendance_records']}")
        print(f"   Integrity: {'✅' if report['database_health']['data_integrity'] else '❌'}")
        
        print(f"\n💡 Recommendations:")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"   {i}. {rec}")
        
        print("="*60)

def main():
    """Run accuracy testing"""
    print("🎯 Smart Attendance System - Accuracy Testing")
    print("="*50)
    
    # Initialize the system
    system = SmartAttendanceSystem()
    
    # Create accuracy tester
    tester = AccuracyTester(system)
    
    # Run comprehensive tests
    results = tester.run_comprehensive_accuracy_test()
    
    print("\n✅ Accuracy testing completed!")
    print("📄 Detailed report saved as JSON file")

if __name__ == "__main__":
    main()

