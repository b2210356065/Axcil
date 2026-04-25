import '../models/api_config.dart';
import '../utils/constants.dart';
import 'api_service.dart';

class ConfigService {
  final ApiService _api = ApiService();

  // Get current config
  Future<ApiConfig> getConfig() async {
    try {
      final response = await _api.get(ApiConstants.config);
      return ApiConfig.fromJson(response.data);
    } catch (e) {
      throw Exception('Failed to load config: $e');
    }
  }

  // Update config
  Future<ApiConfig> updateConfig(ApiConfig config) async {
    try {
      final response = await _api.post(
        ApiConstants.config,
        data: config.toJson(),
      );
      return ApiConfig.fromJson(response.data);
    } catch (e) {
      throw Exception('Failed to update config: $e');
    }
  }

  // Test API key
  Future<bool> testApiKey(String provider, String apiKey) async {
    try {
      final response = await _api.post(
        '${ApiConstants.config}/test',
        data: {'provider': provider, 'api_key': apiKey},
      );
      return response.data['valid'] == true;
    } catch (e) {
      return false;
    }
  }
}
