class Student {
  final String studentId;
  final String studentName;
  final String registeredDate;
  final int imageCount;
  final int totalEncodings;

  Student({
    required this.studentId,
    required this.studentName,
    required this.registeredDate,
    required this.imageCount,
    required this.totalEncodings,
  });

  factory Student.fromJson(Map<String, dynamic> json) {
    return Student(
      studentId: json['student_id'] ?? '',
      studentName: json['student_name'] ?? '',
      registeredDate: json['registered_date'] ?? '',
      imageCount: json['image_count'] ?? 0,
      totalEncodings: json['total_encodings'] ?? 0,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'student_id': studentId,
      'student_name': studentName,
      'registered_date': registeredDate,
      'image_count': imageCount,
      'total_encodings': totalEncodings,
    };
  }
}

class RecognizedStudent {
  final String studentId;
  final String studentName;
  final double confidence;
  final List<int> faceLocation;

  RecognizedStudent({
    required this.studentId,
    required this.studentName,
    required this.confidence,
    required this.faceLocation,
  });

  factory RecognizedStudent.fromJson(Map<String, dynamic> json) {
    return RecognizedStudent(
      studentId: json['student_id'] ?? '',
      studentName: json['student_name'] ?? '',
      confidence: (json['confidence'] ?? 0.0).toDouble(),
      faceLocation: List<int>.from(json['face_location'] ?? []),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'student_id': studentId,
      'student_name': studentName,
      'confidence': confidence,
      'face_location': faceLocation,
    };
  }
}

class AttendanceRecord {
  final String sessionId;
  final String timestamp;
  final int totalFaces;
  final int recognizedCount;
  final int unknownFaces;
  final String csvFile;
  final List<RecognizedStudent> recognizedStudents;

  AttendanceRecord({
    required this.sessionId,
    required this.timestamp,
    required this.totalFaces,
    required this.recognizedCount,
    required this.unknownFaces,
    required this.csvFile,
    required this.recognizedStudents,
  });

  factory AttendanceRecord.fromJson(Map<String, dynamic> json) {
    return AttendanceRecord(
      sessionId: json['session_id'] ?? '',
      timestamp: json['timestamp'] ?? '',
      totalFaces: json['total_faces'] ?? 0,
      recognizedCount: json['recognized_count'] ?? 0,
      unknownFaces: json['unknown_faces'] ?? 0,
      csvFile: json['csv_file'] ?? '',
      recognizedStudents: (json['recognized_students'] as List? ?? [])
          .map((student) => RecognizedStudent.fromJson(student))
          .toList(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'session_id': sessionId,
      'timestamp': timestamp,
      'total_faces': totalFaces,
      'recognized_count': recognizedCount,
      'unknown_faces': unknownFaces,
      'csv_file': csvFile,
      'recognized_students': recognizedStudents.map((s) => s.toJson()).toList(),
    };
  }
}

class CsvFile {
  final String filename;
  final int size;
  final String createdDate;
  final String modifiedDate;
  final String downloadUrl;

  CsvFile({
    required this.filename,
    required this.size,
    required this.createdDate,
    required this.modifiedDate,
    required this.downloadUrl,
  });

  factory CsvFile.fromJson(Map<String, dynamic> json) {
    return CsvFile(
      filename: json['filename'] ?? '',
      size: json['size'] ?? 0,
      createdDate: json['created_date'] ?? '',
      modifiedDate: json['modified_date'] ?? '',
      downloadUrl: json['download_url'] ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'filename': filename,
      'size': size,
      'created_date': createdDate,
      'modified_date': modifiedDate,
      'download_url': downloadUrl,
    };
  }

  String get formattedSize {
    if (size < 1024) return '${size}B';
    if (size < 1024 * 1024) return '${(size / 1024).toStringAsFixed(1)}KB';
    return '${(size / (1024 * 1024)).toStringAsFixed(1)}MB';
  }

  String get formattedDate {
    try {
      final date = DateTime.parse(createdDate);
      return '${date.day}/${date.month}/${date.year} ${date.hour}:${date.minute.toString().padLeft(2, '0')}';
    } catch (e) {
      return createdDate;
    }
  }
}

class AttendanceResult {
  final bool success;
  final String? message;
  final AttendanceRecord attendanceRecord;
  final String? timestamp;
  final String? sessionId;

  AttendanceResult({
    required this.success,
    this.message,
    required this.attendanceRecord,
    this.timestamp,
    this.sessionId,
  });

  factory AttendanceResult.fromJson(Map<String, dynamic> json) {
    return AttendanceResult(
      success: json['success'] ?? false,
      message: json['message'],
      attendanceRecord: AttendanceRecord.fromJson(json['attendance_record']),
      timestamp: json['timestamp'],
      sessionId: json['session_id'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'success': success,
      'message': message,
      'attendance_record': attendanceRecord.toJson(),
      'timestamp': timestamp,
      'session_id': sessionId,
    };
  }
}

class AttendanceHistory {
  final String filename;
  final String date;
  final String time;
  final int totalPresent;
  final List<Map<String, dynamic>> students;
  final String created;

  AttendanceHistory({
    required this.filename,
    required this.date,
    required this.time,
    required this.totalPresent,
    required this.students,
    required this.created,
  });

  factory AttendanceHistory.fromJson(Map<String, dynamic> json) {
    return AttendanceHistory(
      filename: json['filename'] ?? '',
      date: json['date'] ?? '',
      time: json['time'] ?? '',
      totalPresent: json['total_present'] ?? 0,
      students: List<Map<String, dynamic>>.from(json['students'] ?? []),
      created: json['created'] ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'filename': filename,
      'date': date,
      'time': time,
      'total_present': totalPresent,
      'students': students,
      'created': created,
    };
  }
}

class HealthStatus {
  final String status;
  final String timestamp;
  final int registeredStudents;
  final int knownEncodings;

  HealthStatus({
    required this.status,
    required this.timestamp,
    required this.registeredStudents,
    required this.knownEncodings,
  });

  factory HealthStatus.fromJson(Map<String, dynamic> json) {
    return HealthStatus(
      status: json['status'] ?? '',
      timestamp: json['timestamp'] ?? '',
      registeredStudents: json['registered_students'] ?? 0,
      knownEncodings: json['known_encodings'] ?? 0,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'status': status,
      'timestamp': timestamp,
      'registered_students': registeredStudents,
      'known_encodings': knownEncodings,
    };
  }
}
