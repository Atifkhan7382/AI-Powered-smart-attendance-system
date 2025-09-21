import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';
import 'package:http/http.dart' as http;
import '../models/attendance_models.dart';

class ApiService {
  static const String baseUrl = 'http://localhost:5000/api';
  
  // Singleton pattern
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;
  ApiService._internal();

  Future<Map<String, dynamic>> healthCheck() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/health'),
        headers: {'Content-Type': 'application/json'},
      );

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Health check failed: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Network error: $e');
    }
  }

  Future<List<Student>> getStudents() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/students'),
        headers: {'Content-Type': 'application/json'},
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        if (data['success']) {
          return (data['students'] as List)
              .map((student) => Student.fromJson(student))
              .toList();
        } else {
          throw Exception(data['message']);
        }
      } else {
        throw Exception('Failed to load students: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Network error: $e');
    }
  }

  Future<List<AttendanceHistory>> getAttendanceHistory() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/attendance-history'),
        headers: {'Content-Type': 'application/json'},
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        if (data['success']) {
          return (data['history'] as List)
              .map((record) => AttendanceHistory.fromJson(record))
              .toList();
        } else {
          throw Exception(data['message']);
        }
      } else {
        throw Exception('Failed to load attendance history: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Network error: $e');
    }
  }

  Future<List<CsvFile>> getAttendanceFiles() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/attendance-files'),
        headers: {'Content-Type': 'application/json'},
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        if (data['success']) {
          return (data['files'] as List)
              .map((file) => CsvFile.fromJson(file))
              .toList();
        } else {
          throw Exception(data['message']);
        }
      } else {
        throw Exception('Failed to load CSV files: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Network error: $e');
    }
  }

  String getCsvDownloadUrl(String filename) {
    return '$baseUrl/download-csv/$filename';
  }

  Future<AttendanceResult> uploadImage(File imageFile) async {
    try {
      var request = http.MultipartRequest(
        'POST',
        Uri.parse('$baseUrl/upload-image'),
      );

      request.files.add(
        await http.MultipartFile.fromPath('file', imageFile.path),
      );

      var streamedResponse = await request.send();
      var response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return AttendanceResult.fromJson(data);
      } else {
        throw Exception('Upload failed: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Upload error: $e');
    }
  }

  Future<AttendanceResult> uploadImageBase64(String base64Image) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/upload-image'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({'image': base64Image}),
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return AttendanceResult.fromJson(data);
      } else {
        throw Exception('Upload failed: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Upload error: $e');
    }
  }


  Future<Uint8List> downloadCsv(String filename) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/download-csv/$filename'),
      );

      if (response.statusCode == 200) {
        return response.bodyBytes;
      } else {
        throw Exception('Download failed: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Download error: $e');
    }
  }

  Future<bool> testConnection() async {
    try {
      await healthCheck();
      return true;
    } catch (e) {
      return false;
    }
  }
}
