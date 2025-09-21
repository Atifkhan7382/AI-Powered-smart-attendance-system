@echo off
echo ================================
echo Smart Attendance System - Flutter App
echo ================================
echo.

echo Checking Flutter installation...
flutter --version
if %errorlevel% neq 0 (
    echo ERROR: Flutter is not installed or not in PATH
    echo Please install Flutter SDK and add it to PATH
    echo Visit: https://flutter.dev/docs/get-started/install
    pause
    exit /b 1
)

echo.
echo Checking Flutter doctor...
flutter doctor --android-licenses > nul 2>&1

echo.
echo Installing Flutter dependencies...
flutter pub get
if %errorlevel% neq 0 (
    echo ERROR: Failed to get Flutter dependencies
    echo Please check pubspec.yaml and try again
    pause
    exit /b 1
)

echo.
echo Checking for connected devices...
flutter devices

echo.
echo ================================
echo Starting Flutter App...
echo ================================
echo.
echo Make sure the backend server is running at:
echo http://localhost:5000
echo.
echo If using a physical device, update the API URL in:
echo lib/services/api_service.dart
echo.
echo Press Ctrl+C to stop the app
echo ================================
echo.

flutter run

echo.
echo App stopped.
pause
