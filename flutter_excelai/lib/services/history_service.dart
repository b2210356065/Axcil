import 'dart:io';
import '../models/tool_result.dart';
import '../utils/constants.dart';
import 'api_service.dart';

class HistoryService {
  final ApiService _api = ApiService();

  // Get all history
  Future<List<ToolResult>> getHistory() async {
    try {
      final response = await _api.get(ApiConstants.history);
      final List data = response.data;
      return data.map((json) => ToolResult.fromJson(json)).toList();
    } catch (e) {
      throw Exception('Failed to load history: $e');
    }
  }

  // Download file
  Future<void> downloadFile(int historyId, String savePath) async {
    try {
      // Backend doesn't have download endpoint yet
      // This is a placeholder
      throw UnimplementedError('Download not implemented in backend yet');
    } catch (e) {
      throw Exception('Failed to download file: $e');
    }
  }

  // Delete file
  Future<void> deleteFile(int historyId) async {
    try {
      await _api.delete('${ApiConstants.history}/$historyId');
    } catch (e) {
      throw Exception('Failed to delete file: $e');
    }
  }
}
