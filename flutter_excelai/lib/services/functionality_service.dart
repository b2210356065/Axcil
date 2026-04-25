import '../models/functionality.dart';
import '../utils/constants.dart';
import 'api_service.dart';

class FunctionalityService {
  final ApiService _api = ApiService();

  // Get all functionalities for a business
  Future<List<Functionality>> getFunctionalities(int businessId) async {
    try {
      final response = await _api.get(
        ApiConstants.functionalities,
        params: {'business_id': businessId},
      );
      final List data = response.data;
      return data.map((json) => Functionality.fromJson(json)).toList();
    } catch (e) {
      throw Exception('Failed to load functionalities: $e');
    }
  }

  // Get functionality by ID
  Future<Functionality> getFunctionality(int id) async {
    try {
      final response = await _api.get('${ApiConstants.functionalities}/$id');
      return Functionality.fromJson(response.data);
    } catch (e) {
      throw Exception('Failed to load functionality: $e');
    }
  }

  // Create functionality
  Future<Map<String, dynamic>> createFunctionality({
    required int businessId,
    required String name,
    required String description,
    List<Map<String, dynamic>>? inputFields,
    Map<String, dynamic>? excelTemplate,
    String? systemPrompt,
    List<int>? dataTypeIds,
  }) async {
    try {
      final response = await _api.post(
        ApiConstants.functionalities,
        data: {
          'business_id': businessId,
          'name': name,
          'description': description,
          'input_fields': inputFields ?? [{"name": "data", "type": "any"}],
          'excel_template': excelTemplate ?? {"type": "general"},
          'system_prompt': systemPrompt,
          'data_type_ids': dataTypeIds ?? [],
        },
      );
      return response.data;
    } catch (e) {
      throw Exception('Failed to create functionality: $e');
    }
  }

  // Update functionality
  Future<Map<String, dynamic>> updateFunctionality(
    int id, {
    required int businessId,
    String? name,
    String? description,
    List<Map<String, dynamic>>? inputFields,
    Map<String, dynamic>? excelTemplate,
    String? systemPrompt,
    List<int>? dataTypeIds,
  }) async {
    try {
      final response = await _api.put(
        '${ApiConstants.functionalities}/$id',
        data: {
          'business_id': businessId,
          if (name != null) 'name': name,
          if (description != null) 'description': description,
          if (inputFields != null) 'input_fields': inputFields,
          if (excelTemplate != null) 'excel_template': excelTemplate,
          if (systemPrompt != null) 'system_prompt': systemPrompt,
          if (dataTypeIds != null) 'data_type_ids': dataTypeIds,
        },
      );
      return response.data;
    } catch (e) {
      throw Exception('Failed to update functionality: $e');
    }
  }

  // Delete functionality
  Future<void> deleteFunctionality(int id) async {
    try {
      await _api.delete('${ApiConstants.functionalities}/$id');
    } catch (e) {
      throw Exception('Failed to delete functionality: $e');
    }
  }

  // Enrich functionality (AI-powered)
  Future<Functionality> enrichFunctionality(int id) async {
    try {
      final response = await _api.post(
        '${ApiConstants.functionalities}/$id/enrich',
      );
      return Functionality.fromJson(response.data);
    } catch (e) {
      throw Exception('Failed to enrich functionality: $e');
    }
  }

  // Generate algorithm (AI-powered)
  Future<String> generateAlgorithm(int id) async {
    try {
      final response = await _api.post(
        '${ApiConstants.functionalities}/$id/generate_algorithm',
      );
      return response.data['algorithm'];
    } catch (e) {
      throw Exception('Failed to generate algorithm: $e');
    }
  }
}
