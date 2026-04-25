import '../models/business_profile.dart';
import '../utils/constants.dart';
import 'api_service.dart';

class BusinessService {
  final ApiService _api = ApiService();

  // Get active business profile (returns as list for compatibility)
  Future<List<BusinessProfile>> getBusinessProfiles() async {
    try {
      final response = await _api.get(ApiConstants.businessProfiles);
      if (response.data == null) {
        return [];
      }
      // Backend returns single business, wrap in list
      return [BusinessProfile.fromJson(response.data)];
    } catch (e) {
      throw Exception('Failed to load business profiles: $e');
    }
  }

  // Get business profile by ID
  Future<BusinessProfile> getBusinessProfile(int id) async {
    try {
      final response = await _api.get('${ApiConstants.businessProfiles}/$id');
      return BusinessProfile.fromJson(response.data);
    } catch (e) {
      throw Exception('Failed to load business profile: $e');
    }
  }

  // Create business profile
  Future<Map<String, dynamic>> createBusinessProfile({
    required String businessName,
    required String businessDescription,
    String? sector,
    bool isActive = true,
  }) async {
    try {
      final response = await _api.post(
        ApiConstants.businessProfiles,
        data: {
          'business_name': businessName,
          'business_description': businessDescription,
          'sector': sector,
          'is_active': isActive,
        },
      );
      return response.data;
    } catch (e) {
      throw Exception('Failed to create business profile: $e');
    }
  }

  // Update business profile (backend doesn't support update yet)
  Future<Map<String, dynamic>> updateBusinessProfile(
    int id, {
    String? businessName,
    String? businessDescription,
    String? sector,
    bool? isActive,
  }) async {
    try {
      final response = await _api.post(
        ApiConstants.businessProfiles,
        data: {
          if (businessName != null) 'business_name': businessName,
          if (businessDescription != null) 'business_description': businessDescription,
          if (sector != null) 'sector': sector,
          if (isActive != null) 'is_active': isActive,
        },
      );
      return response.data;
    } catch (e) {
      throw Exception('Failed to update business profile: $e');
    }
  }

  // Delete business profile
  Future<void> deleteBusinessProfile(int id) async {
    try {
      await _api.delete('${ApiConstants.businessProfiles}/$id');
    } catch (e) {
      throw Exception('Failed to delete business profile: $e');
    }
  }
}
