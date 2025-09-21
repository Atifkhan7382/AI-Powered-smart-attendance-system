import 'dart:io';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:path_provider/path_provider.dart';
import 'package:intl/intl.dart';
import 'package:url_launcher/url_launcher.dart';
import '../models/attendance_models.dart';
import '../services/api_service.dart';

class AttendanceResultScreen extends StatefulWidget {
  final AttendanceResult result;

  const AttendanceResultScreen({
    super.key,
    required this.result,
  });

  @override
  State<AttendanceResultScreen> createState() => _AttendanceResultScreenState();
}

class _AttendanceResultScreenState extends State<AttendanceResultScreen> {
  final ApiService _apiService = ApiService();
  bool _isDownloading = false;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Attendance Results'),
        backgroundColor: const Color(0xFF1976D2),
        actions: [
          if (widget.result.attendanceRecord.csvFile.isNotEmpty)
            IconButton(
              icon: const Icon(Icons.download),
              onPressed: _isDownloading ? null : _downloadCsv,
              tooltip: 'Download CSV',
            ),
          IconButton(
            icon: const Icon(Icons.share),
            onPressed: _shareResults,
            tooltip: 'Share Results',
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildSummaryCard(),
            const SizedBox(height: 20),
            if (widget.result.attendanceRecord.recognizedStudents.isNotEmpty) ...[
              _buildStudentsList(),
              const SizedBox(height: 20),
            ],
            _buildDetailsCard(),
            const SizedBox(height: 20),
            _buildActionButtons(),
          ],
        ),
      ),
    );
  }

  Widget _buildSummaryCard() {
    return Card(
      color: widget.result.success ? Colors.green[50] : Colors.red[50],
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  widget.result.success ? Icons.check_circle : Icons.error,
                  color: widget.result.success ? Colors.green : Colors.red,
                  size: 28,
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    widget.result.success ? 'Attendance Processed Successfully' : 'Processing Failed',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                      color: widget.result.success ? Colors.green[700] : Colors.red[700],
                    ),
                  ),
                ),
              ],
            ),
            if (widget.result.message != null) ...[
              const SizedBox(height: 8),
              Text(
                widget.result.message!,
                style: TextStyle(
                  color: widget.result.success ? Colors.green[600] : Colors.red[600],
                ),
              ),
            ],
            if (widget.result.success) ...[
              const SizedBox(height: 16),
              Row(
                children: [
                  Expanded(
                    child: _buildStatItem(
                      'Total Faces',
                      '${widget.result.attendanceRecord.totalFaces}',
                      Icons.face,
                      Colors.blue,
                    ),
                  ),
                  Expanded(
                    child: _buildStatItem(
                      'Recognized',
                      '${widget.result.attendanceRecord.recognizedCount}',
                      Icons.person,
                      Colors.green,
                    ),
                  ),
                  Expanded(
                    child: _buildStatItem(
                      'Unknown',
                      '${widget.result.attendanceRecord.unknownFaces}',
                      Icons.person_outline,
                      Colors.orange,
                    ),
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildStatItem(String label, String value, IconData icon, Color color) {
    return Column(
      children: [
        Icon(icon, color: color, size: 24),
        const SizedBox(height: 4),
        Text(
          value,
          style: TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.bold,
            color: color,
          ),
        ),
        Text(
          label,
          style: TextStyle(
            fontSize: 12,
            color: Colors.grey[600],
          ),
          textAlign: TextAlign.center,
        ),
      ],
    );
  }

  Widget _buildStudentsList() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.people, color: Color(0xFF1976D2)),
                const SizedBox(width: 8),
                const Text(
                  'Students Present',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const Spacer(),
                Chip(
                  label: Text('${widget.result.attendanceRecord.recognizedStudents.length}'),
                  backgroundColor: Colors.green[100],
                  labelStyle: TextStyle(
                    color: Colors.green[700],
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            ListView.separated(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: widget.result.attendanceRecord.recognizedStudents.length,
              separatorBuilder: (context, index) => const Divider(height: 1),
              itemBuilder: (context, index) {
                final student = widget.result.attendanceRecord.recognizedStudents[index];
                return ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: CircleAvatar(
                    backgroundColor: Colors.green[100],
                    child: Text(
                      student.studentName.isNotEmpty 
                          ? student.studentName[0].toUpperCase()
                          : '?',
                      style: TextStyle(
                        color: Colors.green[700],
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                  title: Text(
                    student.studentName,
                    style: const TextStyle(fontWeight: FontWeight.w500),
                  ),
                  subtitle: Text('ID: ${student.studentId}'),
                  trailing: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: _getConfidenceColor(student.confidence),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      '${(student.confidence * 100).toStringAsFixed(1)}%',
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                );
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDetailsCard() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Session Details',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 16),
            _buildDetailRow('Session ID', widget.result.sessionId ?? 'N/A'),
            _buildDetailRow('Timestamp', _formatTimestamp(widget.result.timestamp)),
            _buildDetailRow('CSV File', widget.result.attendanceRecord.csvFile.isNotEmpty ? widget.result.attendanceRecord.csvFile : 'Not generated'),
            if (widget.result.success) ...[
              _buildDetailRow('Recognition Rate', 
                '${((widget.result.attendanceRecord.recognizedCount / widget.result.attendanceRecord.totalFaces) * 100).toStringAsFixed(1)}%'),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildDetailRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4.0),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 100,
            child: Text(
              label,
              style: TextStyle(
                color: Colors.grey[600],
                fontSize: 14,
              ),
            ),
          ),
          const Text(': '),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(
                fontWeight: FontWeight.w500,
                fontSize: 14,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildActionButtons() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        if (widget.result.attendanceRecord.csvFile.isNotEmpty) ...[
          ElevatedButton.icon(
            onPressed: _isDownloading ? null : _downloadCsv,
            icon: _isDownloading
                ? const SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                    ),
                  )
                : const Icon(Icons.download),
            label: Text(_isDownloading ? 'Downloading...' : 'Download CSV File'),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.green,
              padding: const EdgeInsets.symmetric(vertical: 16),
            ),
          ),
          const SizedBox(height: 12),
        ],
        OutlinedButton.icon(
          onPressed: () => Navigator.of(context).pop(),
          icon: const Icon(Icons.camera_alt),
          label: const Text('Take Another Photo'),
          style: OutlinedButton.styleFrom(
            padding: const EdgeInsets.symmetric(vertical: 16),
          ),
        ),
        const SizedBox(height: 12),
        TextButton.icon(
          onPressed: () => Navigator.of(context).popUntil((route) => route.isFirst),
          icon: const Icon(Icons.home),
          label: const Text('Back to Home'),
        ),
      ],
    );
  }

  Color _getConfidenceColor(double confidence) {
    if (confidence >= 0.8) return Colors.green;
    if (confidence >= 0.6) return Colors.orange;
    return Colors.red;
  }

  String _formatTimestamp(String? timestamp) {
    if (timestamp == null) return 'N/A';
    
    try {
      final dateTime = DateTime.parse(timestamp);
      return DateFormat('MMM dd, yyyy HH:mm:ss').format(dateTime);
    } catch (e) {
      return timestamp;
    }
  }

  Future<void> _downloadCsv() async {
    if (widget.result.attendanceRecord.csvFile.isEmpty) return;

    setState(() {
      _isDownloading = true;
    });

    try {
      final url = _apiService.getCsvDownloadUrl(widget.result.attendanceRecord.csvFile);
      
      if (kIsWeb) {
        // For web, open in new tab
        if (await canLaunchUrl(Uri.parse(url))) {
          await launchUrl(
            Uri.parse(url),
            mode: LaunchMode.externalApplication,
          );
          
          if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(
                content: Text('Download started in new tab'),
                backgroundColor: Colors.green,
                duration: Duration(seconds: 2),
              ),
            );
          }
        } else {
          throw Exception('Could not launch download URL');
        }
      } else {
        // For mobile/desktop, use url_launcher
        if (await canLaunchUrl(Uri.parse(url))) {
          await launchUrl(Uri.parse(url));
          
          if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text('Downloading ${widget.result.attendanceRecord.csvFile}'),
                backgroundColor: Colors.green,
                duration: const Duration(seconds: 2),
              ),
            );
          }
        } else {
          throw Exception('Could not launch download URL');
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error downloading CSV: $e'),
            backgroundColor: Colors.red,
            duration: const Duration(seconds: 3),
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _isDownloading = false;
        });
      }
    }
  }

  Future<void> _shareResults() async {
    final text = '''
Attendance Results
==================
Date: ${_formatTimestamp(widget.result.timestamp)}
Total Faces: ${widget.result.attendanceRecord.totalFaces}
Recognized: ${widget.result.attendanceRecord.recognizedCount}
Unknown: ${widget.result.attendanceRecord.unknownFaces}

Students Recognized:
${widget.result.attendanceRecord.recognizedStudents.map((s) => '• ${s.studentName} (${s.studentId}) - ${(s.confidence * 100).toStringAsFixed(1)}%').join('\n')}
''';

    await Clipboard.setData(ClipboardData(text: text));
    
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Results copied to clipboard'),
          duration: Duration(seconds: 2),
        ),
      );
    }
  }
}
