# Smart Attendance System - Complete Setup Guide

## Overview
This system consists of:
1. **Python Backend**: Face recognition and attendance processing
2. **Flask API**: RESTful API server for frontend communication
3. **Flutter Frontend**: Mobile/desktop app for attendance management

## Quick Start

### 1. Backend Setup (Required First)

1. **Navigate to the backend directory**:
   ```bash
   cd attendance_project
   ```

2. **Run the startup script**:
   ```bash
   start_server.bat
   ```
   
   This will:
   - Create a virtual environment
   - Install all dependencies
   - Verify system setup
   - Start the Flask API server

3. **Alternative manual setup**:
   ```bash
   # Create virtual environment
   python -m venv venv
   venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Start the server
   python flask_api.py
   ```

### 2. Flutter Frontend Setup

1. **Navigate to Flutter app directory**:
   ```bash
   cd flutter_attendance_app
   ```

2. **Install dependencies**:
   ```bash
   flutter pub get
   ```

3. **Run the app**:
   ```bash
   flutter run
   ```

## Detailed Setup Instructions

### Prerequisites

#### For Backend:
- Python 3.8 or higher
- pip (Python package manager)
- At least 2GB free disk space
- Webcam or camera (for testing)

#### For Frontend:
- Flutter SDK 3.0.0+
- Android Studio or VS Code
- Android SDK (for Android development)
- Xcode (for iOS development on macOS)

### Backend Configuration

#### 1. Directory Structure
Ensure your directory structure looks like this:
```
attendance_project/
├── student_photos/          # Student registration photos
│   ├── student_001/         # Individual student folders
│   ├── student_002/
│   └── ...
├── classroom_photos/        # Classroom photos for attendance
├── attendance_records/      # Generated CSV files
├── models/                  # Face encodings and models
├── logs/                    # System logs
├── smart_attendance_system.py
├── flask_api.py
├── requirements.txt
└── start_server.bat
```

#### 2. Student Registration
Before using the system, you need to register students:

1. **Add student photos**:
   - Create folders in `student_photos/` named like `student_001`, `student_002`, etc.
   - Add 3-5 clear photos of each student's face
   - Supported formats: JPG, PNG, JPEG

2. **Register students**:
   ```bash
   python smart_attendance_system.py
   # Choose option 2: Register All Students
   ```

#### 3. API Server Configuration
The Flask API runs on `http://localhost:5000` by default. Key endpoints:

- `GET /api/health` - System status
- `GET /api/students` - List registered students
- `POST /api/upload-image` - Process attendance image
- `GET /api/attendance-history` - Get attendance records
- `GET /api/download-csv/<filename>` - Download CSV files

### Frontend Configuration

#### 1. API Connection
Update the API URL in `lib/services/api_service.dart` if needed:
```dart
static const String baseUrl = 'http://localhost:5000/api';
```

For physical devices, replace `localhost` with your computer's IP address.

#### 2. Permissions
The app requires these permissions (already configured):
- Camera access
- Storage access
- Internet access

## Usage Workflow

### 1. System Startup
1. Start the backend server using `start_server.bat`
2. Wait for "Server starting on http://localhost:5000" message
3. Launch the Flutter app
4. Check connection status on home screen

### 2. Taking Attendance
1. Open the Flutter app
2. Tap "Take Attendance"
3. Choose image source:
   - **Camera**: Take a new photo
   - **Gallery**: Select existing photo
   - **Files**: Browse for image files
4. Select a classroom photo with visible faces
5. Tap "Process Attendance"
6. View results showing:
   - Number of faces detected
   - Recognized students
   - Unknown faces
   - Confidence scores
7. Download CSV file with attendance data

### 3. Managing Students
1. Tap "Students" to view registered students
2. Search by name or ID
3. View student details including:
   - Registration date
   - Number of training images
   - Face encodings count

### 4. Viewing History
1. Tap "History" to see past attendance sessions
2. Filter by date or number of records
3. Expand records to see details
4. Download CSV files for specific sessions

## File Outputs

### CSV Format
Generated CSV files contain:
```csv
Date,Time,Student_ID,Student_Name,Status,Confidence,Timestamp
2025-09-21,06:00:15,STUDENT_001,John Doe,Present,0.85,2025-09-21T06:00:15
```

### File Locations
- **Attendance CSVs**: `attendance_project/attendance_records/`
- **Session summaries**: `attendance_project/attendance_records/` (JSON format)
- **System logs**: `attendance_project/logs/`
- **Downloaded files** (mobile): Device's Downloads folder

## Troubleshooting

### Backend Issues

#### "Module not found" errors:
```bash
# Activate virtual environment first
venv\Scripts\activate
pip install -r requirements.txt
```

#### "No faces detected":
- Ensure good lighting in photos
- Use clear, high-resolution images
- Make sure faces are clearly visible
- Try different angles or distances

#### "No students registered":
- Add student photos to `student_photos/` directory
- Run student registration process
- Check logs for registration errors

### Frontend Issues

#### "Connection failed":
- Verify backend server is running
- Check API URL in `api_service.dart`
- For physical devices, use computer's IP instead of localhost
- Ensure firewall allows connections on port 5000

#### Camera not working:
- Grant camera permissions in device settings
- Restart the app after granting permissions
- Try using gallery/file picker instead

#### Download issues:
- Grant storage permissions
- Check available storage space
- Verify backend server is accessible

### Performance Issues

#### Slow face recognition:
- Reduce image size before processing
- Use fewer training images per student
- Close other resource-intensive applications

#### App crashes:
- Check device memory
- Restart the app
- Clear app cache/data

## Advanced Configuration

### Custom API Port
To change the API port, edit `flask_api.py`:
```python
app.run(host='0.0.0.0', port=8080, debug=True)  # Change port here
```

Also update the Flutter app's API URL accordingly.

### Face Recognition Tuning
Adjust recognition parameters in `smart_attendance_system.py`:
```python
self.face_recognition_tolerance = 0.6  # Lower = stricter matching
self.min_face_size = 40  # Minimum face size in pixels
```

### Database Integration
The system can be extended to use databases instead of CSV files by modifying the `save_attendance_record` function in `flask_api.py`.

## Security Considerations

1. **Network Security**: Use HTTPS in production
2. **File Permissions**: Restrict access to student photos
3. **Data Privacy**: Implement proper data handling policies
4. **Authentication**: Add user authentication for production use

## Development

### Adding New Features
1. **Backend**: Extend `flask_api.py` with new endpoints
2. **Frontend**: Add new screens in `lib/screens/`
3. **Models**: Update data models in `lib/models/`

### Testing
- Test with various lighting conditions
- Try different camera angles
- Test with groups of different sizes
- Verify CSV output format

## Support

### Common Solutions
1. **Restart both backend and frontend** for connection issues
2. **Check file permissions** for file access errors
3. **Verify Python/Flutter versions** for compatibility issues
4. **Review logs** in `attendance_project/logs/` for detailed error information

### Getting Help
1. Check this setup guide thoroughly
2. Review error messages in logs
3. Verify all prerequisites are installed
4. Test with sample data first

## Version Information
- Backend: Python 3.8+ with OpenCV, face_recognition
- Frontend: Flutter 3.0+ with Dart
- API: Flask 2.3+ with CORS support
- Database: File-based (CSV/JSON) with optional database integration
