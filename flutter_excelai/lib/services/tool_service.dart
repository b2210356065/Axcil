import 'dart:io';
import '../utils/constants.dart';
import 'api_service.dart';

class ToolService {
  final ApiService _api = ApiService();

  // Execute tool
  Future<Map<String, dynamic>> executeTool({
    required String toolType,
    required int businessId,
    required int functionalityId,
    File? file,
    String? text,
    Map<String, dynamic>? formData,
  }) async {
    try {
      final data = {
        'tool_type': toolType,
        'business_id': businessId,
        'functionality_id': functionalityId,
        if (text != null) 'text': text,
        if (formData != null) 'form_data': formData,
      };

      if (file != null) {
        return (await _api.uploadFile(
          '${ApiConstants.tools}/execute',
          file.path,
          data: data,
        )).data;
      } else {
        return (await _api.post(
          '${ApiConstants.tools}/execute',
          data: data,
        )).data;
      }
    } catch (e) {
      throw Exception('Failed to execute tool: $e');
    }
  }

  // Get tool status
  Future<Map<String, dynamic>> getToolStatus(String taskId) async {
    try {
      final response = await _api.get('${ApiConstants.tools}/status/$taskId');
      return response.data;
    } catch (e) {
      throw Exception('Failed to get tool status: $e');
    }
  }
}
