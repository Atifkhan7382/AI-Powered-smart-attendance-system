# Smart Attendance System - Flutter Frontend

A modern Flutter application for the Smart Attendance System that integrates with a Python Flask backend for face recognition-based attendance tracking.

## Features

- 📸 **Image Upload**: Take photos or select from gallery for attendance
- 🔍 **Face Recognition**: Automatic face detection and recognition
- 👥 **Student Management**: View registered students and their details
- 📊 **Attendance History**: View past attendance records
- 📄 **CSV Export**: Download attendance data as CSV files
- 🎨 **Modern UI**: Clean and intuitive user interface
- 📱 **Cross-platform**: Works on Android and iOS

## Screenshots

The app includes:
- Home dashboard with system status
- Image upload screen with camera/gallery options
- Attendance results with recognized students
- Student list with search functionality
- History screen with downloadable CSV files

## Prerequisites

- Flutter SDK (3.0.0 or higher)
- Dart SDK
- Android Studio / VS Code
- Python Flask backend running (see backend setup)

## Backend Setup

1. **Install Python dependencies**:
   ```bash
   cd attendance_project
   pip install -r requirements.txt
   ```

2. **Start the Flask API server**:
   ```bash
   python flask_api.py
   ```

   The server will start on `http://localhost:5000`

3. **Ensure your attendance system is set up**:
   - Student photos should be in the `student_photos` directory
   - Run the registration process to create face encodings
   - Verify the system status using the backend

## Flutter App Setup

1. **Clone and navigate to the Flutter app directory**:
   ```bash
   cd flutter_attendance_app
   ```

2. **Install Flutter dependencies**:
   ```bash
   flutter pub get
   ```

3. **Update API endpoint** (if needed):
   - Open `lib/services/api_service.dart`
   - Update the `baseUrl` if your Flask server is running on a different address

4. **Run the app**:
   ```bash
   flutter run
   ```

## Project Structure

```
flutter_attendance_app/
├── lib/
│   ├── main.dart                 # App entry point
│   ├── models/
│   │   └── attendance_models.dart # Data models
│   ├── services/
│   │   └── api_service.dart      # API communication
│   └── screens/
│       ├── home_screen.dart      # Dashboard
│       ├── upload_screen.dart    # Image upload
│       ├── attendance_result_screen.dart # Results
│       ├── students_screen.dart  # Student list
│       └── history_screen.dart   # Attendance history
├── android/                      # Android configuration
├── pubspec.yaml                  # Dependencies
└── README.md                     # This file
```

## API Endpoints

The Flutter app communicates with these Flask API endpoints:

- `GET /api/health` - System health check
- `GET /api/students` - Get registered students
- `POST /api/upload-image` - Upload image for attendance
- `GET /api/attendance-history` - Get attendance history
- `GET /api/download-csv/<filename>` - Download CSV file

## Configuration

### API Service Configuration

Update the API base URL in `lib/services/api_service.dart`:

```dart
static const String baseUrl = 'http://your-server-ip:5000/api';
```

### Permissions

The app requires these permissions (already configured):
- Camera access
- Storage access
- Internet access

## Usage

1. **Start the Flask backend server**
2. **Launch the Flutter app**
3. **Check system status** on the home screen
4. **Take attendance**:
   - Tap "Take Attendance"
   - Choose camera or gallery
   - Select a classroom photo
   - Process the image
   - View results and download CSV
5. **View students** to see registered students
6. **Check history** for past attendance records

## Troubleshooting

### Connection Issues
- Ensure Flask server is running on `http://localhost:5000`
- Check if your device/emulator can reach the server
- For physical devices, use your computer's IP address instead of localhost

### Camera Issues
- Grant camera permissions in device settings
- Ensure camera is not being used by another app

### File Download Issues
- Grant storage permissions
- Check available storage space

## Development

### Adding New Features

1. **Models**: Add new data models in `lib/models/`
2. **API calls**: Extend `ApiService` in `lib/services/api_service.dart`
3. **UI screens**: Create new screens in `lib/screens/`
4. **Navigation**: Update navigation in existing screens

### Testing

```bash
# Run tests
flutter test

# Run integration tests
flutter drive --target=test_driver/app.dart
```

## Building for Production

### Android
```bash
flutter build apk --release
# or
flutter build appbundle --release
```

### iOS
```bash
flutter build ios --release
```

## Dependencies

Key Flutter packages used:
- `http`: API communication
- `image_picker`: Camera and gallery access
- `file_picker`: File selection
- `flutter_spinkit`: Loading animations
- `intl`: Date formatting
- `path_provider`: File system access

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is part of the Smart Attendance System and follows the same licensing terms.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Verify backend server is running
3. Check Flutter and Dart SDK versions
4. Review device permissions

## Version History

- **v1.0.0**: Initial release with core features
  - Image upload and processing
  - Student management
  - Attendance history
  - CSV export functionality
