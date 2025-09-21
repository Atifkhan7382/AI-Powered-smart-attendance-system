from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import cv2
import numpy as np
import face_recognition
import pandas as pd
from datetime import datetime, date
import json
import logging
import uuid
from werkzeug.utils import secure_filename
import io
import base64
from PIL import Image
import tempfile
from smart_attendance_system import OptimizedAttendanceSystem

app = Flask(__name__)
CORS(app)  # Enable CORS for Flutter app

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize attendance system
attendance_system = OptimizedAttendanceSystem()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_base64_image(base64_string):
    """Convert base64 string to image and save temporarily"""
    try:
        # Remove data URL prefix if present
        if base64_string.startswith('data:image'):
            base64_string = base64_string.split(',')[1]
        
        # Decode base64
        image_data = base64.b64decode(base64_string)
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        temp_file.write(image_data)
        temp_file.close()
        
        return temp_file.name
    except Exception as e:
        logger.error(f"Error processing base64 image: {str(e)}")
        return None

def recognize_faces_in_image(image_path):
    """Recognize faces in uploaded image using the attendance system"""
    try:
        # Load and preprocess image
        image = attendance_system.fast_preprocess_image(image_path)
        
        # Detect faces
        face_locations = attendance_system.fast_face_detection(image)
        
        if not face_locations:
            return {
                'success': False,
                'message': 'No faces detected in the image',
                'recognized_students': [],
                'total_faces': 0
            }
        
        # Get face encodings for ALL detected faces (balanced for accuracy)
        face_encodings = face_recognition.face_encodings(
            image, 
            face_locations,
            num_jitters=1,  # Some jitters for better accuracy
            model="large"   # Use large model for better accuracy
        )
        
        recognized_students = []
        unknown_faces = 0
        recognized_student_ids = set()  # Track already recognized students to avoid duplicates
        
        logger.info(f"Processing {len(face_encodings)} face encodings from {len(face_locations)} detected faces")
        
        for i, face_encoding in enumerate(face_encodings):
            # Compare with known faces
            matches = face_recognition.compare_faces(
                attendance_system.known_face_encodings, 
                face_encoding,
                tolerance=attendance_system.face_recognition_tolerance
            )
            
            if True in matches:
                # Find the best match
                face_distances = face_recognition.face_distance(
                    attendance_system.known_face_encodings, 
                    face_encoding
                )
                best_match_index = np.argmin(face_distances)
                
                if matches[best_match_index]:
                    student_id = attendance_system.known_face_names[best_match_index]
                    
                    # Avoid duplicate recognition of the same student
                    if student_id not in recognized_student_ids:
                        student_info = attendance_system.student_database.get(student_id, {})
                        confidence = float(1 - face_distances[best_match_index])
                        
                        # Only add if confidence is above a reasonable threshold
                        if confidence > 0.35:  # Lower threshold for better detection
                            # Convert numpy integers to regular Python integers for JSON serialization
                            face_loc = face_locations[i]
                            recognized_students.append({
                                'student_id': student_id,
                                'student_name': student_info.get('name', 'Unknown'),
                                'confidence': confidence,
                                'face_location': [int(face_loc[0]), int(face_loc[1]), int(face_loc[2]), int(face_loc[3])]
                            })
                            recognized_student_ids.add(student_id)
                            logger.info(f"Recognized: {student_info.get('name', 'Unknown')} (ID: {student_id}) with confidence {confidence:.2f}")
                        else:
                            unknown_faces += 1
                            logger.debug(f"Low confidence match for student {student_id}: {confidence:.2f}")
                    else:
                        logger.debug(f"Student {student_id} already recognized, skipping duplicate")
                else:
                    unknown_faces += 1
            else:
                unknown_faces += 1
                logger.debug(f"No match found for face {i+1}")
        
        return {
            'success': True,
            'recognized_students': recognized_students,
            'total_faces': int(len(face_locations)),
            'recognized_count': int(len(recognized_students)),
            'unknown_faces': int(unknown_faces),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error recognizing faces: {str(e)}")
        return {
            'success': False,
            'message': f'Error processing image: {str(e)}',
            'recognized_students': [],
            'total_faces': 0
        }

def save_attendance_record(attendance_data):
    """Save attendance record to CSV and database"""
    try:
        # Create attendance record
        timestamp = datetime.now()
        date_str = timestamp.strftime('%Y-%m-%d')
        time_str = timestamp.strftime('%H:%M:%S')
        
        # Prepare data for CSV
        attendance_records = []
        for student in attendance_data['recognized_students']:
            record = {
                'Date': date_str,
                'Time': time_str,
                'Student_ID': student['student_id'],
                'Student_Name': student['student_name'],
                'Status': 'Present',
                'Confidence': f"{student['confidence']:.2f}",
                'Timestamp': attendance_data['timestamp']
            }
            attendance_records.append(record)
        
        # Save to CSV
        csv_filename = f"attendance_{date_str}_{timestamp.strftime('%H%M%S')}.csv"
        csv_path = os.path.join(attendance_system.attendance_path, csv_filename)
        
        df = pd.DataFrame(attendance_records)
        df.to_csv(csv_path, index=False)
        
        # Also save summary
        summary = {
            'session_id': str(uuid.uuid4()),
            'timestamp': attendance_data['timestamp'],
            'total_faces': attendance_data['total_faces'],
            'recognized_count': attendance_data['recognized_count'],
            'unknown_faces': attendance_data['unknown_faces'],
            'students_present': [s['student_id'] for s in attendance_data['recognized_students']],
            'csv_file': csv_filename
        }
        
        summary_filename = f"session_summary_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        summary_path = os.path.join(attendance_system.attendance_path, summary_filename)
        
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        return {
            'success': True,
            'csv_file': csv_filename,
            'csv_path': csv_path,
            'summary_file': summary_filename,
            'session_id': summary['session_id']
        }
        
    except Exception as e:
        logger.error(f"Error saving attendance record: {str(e)}")
        return {
            'success': False,
            'message': f'Error saving attendance: {str(e)}'
        }

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'registered_students': len(attendance_system.student_database),
        'known_encodings': len(attendance_system.known_face_encodings)
    })

@app.route('/api/students', methods=['GET'])
def get_students():
    """Get list of registered students"""
    try:
        students = []
        for student_id, data in attendance_system.student_database.items():
            students.append({
                'student_id': student_id,
                'student_name': data.get('name', 'Unknown'),
                'registered_date': data.get('registered_date', ''),
                'image_count': data.get('image_count', 0),
                'total_encodings': data.get('total_encodings', 0)
            })
        
        return jsonify({
            'success': True,
            'students': students,
            'total_count': len(students)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/upload-image', methods=['POST'])
def upload_image():
    """Handle image upload and process attendance"""
    try:
        image_path = None
        
        # Handle file upload
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(image_path)
        
        # Handle base64 image
        elif request.is_json:
            data = request.get_json()
            if 'image' in data:
                image_path = process_base64_image(data['image'])
        
        if not image_path:
            return jsonify({
                'success': False,
                'message': 'No valid image provided',
                'attendance_record': {
                    'session_id': '',
                    'timestamp': datetime.now().isoformat(),
                    'total_faces': 0,
                    'recognized_count': 0,
                    'unknown_faces': 0,
                    'csv_file': '',
                    'recognized_students': []
                }
            }), 400
        
        # Process the image for face recognition
        attendance_data = recognize_faces_in_image(image_path)
        
        session_id = None
        csv_file = None
        
        if attendance_data['success'] and attendance_data['recognized_students']:
            # Save attendance record
            save_result = save_attendance_record(attendance_data)
            if save_result['success']:
                session_id = save_result.get('session_id')
                csv_file = save_result.get('csv_file')
        
        # Clean up temporary file
        if image_path and os.path.exists(image_path):
            try:
                os.unlink(image_path)
            except:
                pass
        
        # Format response to match AttendanceResult model expectations
        response = {
            'success': attendance_data['success'],
            'message': attendance_data.get('message'),
            'timestamp': attendance_data.get('timestamp'),
            'session_id': session_id,
            'attendance_record': {
                'session_id': session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'timestamp': attendance_data.get('timestamp', datetime.now().isoformat()),
                'total_faces': attendance_data.get('total_faces', 0),
                'recognized_count': attendance_data.get('recognized_count', 0),
                'unknown_faces': attendance_data.get('unknown_faces', 0),
                'csv_file': csv_file or '',
                'recognized_students': attendance_data.get('recognized_students', [])
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in upload_image: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Server error: {str(e)}',
            'attendance_record': {
                'session_id': '',
                'timestamp': datetime.now().isoformat(),
                'total_faces': 0,
                'recognized_count': 0,
                'unknown_faces': 0,
                'csv_file': '',
                'recognized_students': []
            }
        }), 500

@app.route('/api/attendance-history', methods=['GET'])
def get_attendance_history():
    """Get attendance history"""
    try:
        # Get query parameters
        date_filter = request.args.get('date')
        limit = int(request.args.get('limit', 10))
        
        attendance_files = []
        
        # Scan attendance directory for CSV files
        for filename in os.listdir(attendance_system.attendance_path):
            if filename.endswith('.csv') and filename.startswith('attendance_'):
                file_path = os.path.join(attendance_system.attendance_path, filename)
                file_stat = os.stat(file_path)
                
                attendance_files.append({
                    'filename': filename,
                    'path': file_path,
                    'created': datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
                    'size': file_stat.st_size
                })
        
        # Sort by creation time (newest first)
        attendance_files.sort(key=lambda x: x['created'], reverse=True)
        
        # Apply limit
        attendance_files = attendance_files[:limit]
        
        # Read summary data if available
        history = []
        for file_info in attendance_files:
            try:
                df = pd.read_csv(file_info['path'])
                summary = {
                    'filename': file_info['filename'],
                    'date': df['Date'].iloc[0] if not df.empty else 'Unknown',
                    'time': df['Time'].iloc[0] if not df.empty else 'Unknown',
                    'total_present': len(df),
                    'students': df[['Student_ID', 'Student_Name']].to_dict('records') if not df.empty else [],
                    'created': file_info['created']
                }
                history.append(summary)
            except Exception as e:
                logger.error(f"Error reading {file_info['filename']}: {str(e)}")
        
        return jsonify({
            'success': True,
            'history': history,
            'total_files': len(history)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/attendance-files', methods=['GET'])
def get_attendance_files():
    """Get list of available attendance CSV files"""
    try:
        csv_files = []
        attendance_dir = attendance_system.attendance_path
        
        if os.path.exists(attendance_dir):
            for filename in os.listdir(attendance_dir):
                if filename.endswith('.csv'):
                    file_path = os.path.join(attendance_dir, filename)
                    file_stats = os.stat(file_path)
                    
                    csv_files.append({
                        'filename': filename,
                        'size': file_stats.st_size,
                        'created_date': datetime.fromtimestamp(file_stats.st_ctime).isoformat(),
                        'modified_date': datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                        'download_url': f'/api/download-csv/{filename}'
                    })
        
        # Sort by creation date (newest first)
        csv_files.sort(key=lambda x: x['created_date'], reverse=True)
        
        return jsonify({
            'success': True,
            'files': csv_files,
            'total_count': len(csv_files)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/download-csv/<filename>', methods=['GET'])
def download_csv(filename):
    """Download specific CSV file"""
    try:
        # Security check - only allow CSV files from attendance directory
        if not filename.endswith('.csv') or '..' in filename:
            return jsonify({'error': 'Invalid filename'}), 400
        
        file_path = os.path.join(attendance_system.attendance_path, filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='text/csv'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/register-student', methods=['POST'])
def register_student():
    """Register a new student (for future enhancement)"""
    try:
        data = request.get_json()
        
        # This would integrate with your existing registration system
        # For now, return a placeholder response
        return jsonify({
            'success': True,
            'message': 'Student registration endpoint - to be implemented',
            'data': data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

if __name__ == '__main__':
    # Initialize the attendance system
    try:
        logger.info("Initializing attendance system...")
        attendance_system.verify_system_setup()
        logger.info(f"Loaded {len(attendance_system.student_database)} students")
        logger.info(f"Server starting on http://localhost:5000")
        
        app.run(host='0.0.0.0', port=5000, debug=True)
        
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        print("Please ensure your attendance system is properly set up and try again.")
