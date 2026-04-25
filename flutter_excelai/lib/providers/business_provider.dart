import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/business_profile.dart';
import '../services/business_service.dart';

final businessServiceProvider = Provider((ref) => BusinessService());

final businessListProvider = FutureProvider<List<BusinessProfile>>((ref) async {
  final service = ref.watch(businessServiceProvider);
  return await service.getBusinessProfiles();
});

final businessNotifierProvider = StateNotifierProvider<BusinessNotifier,
    AsyncValue<List<BusinessProfile>>>((ref) {
  return BusinessNotifier(ref.watch(businessServiceProvider));
});

class BusinessNotifier
    extends StateNotifier<AsyncValue<List<BusinessProfile>>> {
  final BusinessService _service;

  BusinessNotifier(this._service) : super(const AsyncValue.loading()) {
    loadBusinessProfiles();
  }

  Future<void> loadBusinessProfiles() async {
    state = const AsyncValue.loading();
    try {
      final profiles = await _service.getBusinessProfiles();
      state = AsyncValue.data(profiles);
    } catch (e, stack) {
      state = AsyncValue.error(e, stack);
    }
  }

  Future<void> createProfile({
    required String businessName,
    required String businessDescription,
    String? sector,
    bool isActive = true,
  }) async {
    try {
      await _service.createBusinessProfile(
        businessName: businessName,
        businessDescription: businessDescription,
        sector: sector,
        isActive: isActive,
      );
      await loadBusinessProfiles();
    } catch (e) {
      // Error handling
    }
  }

  Future<void> updateProfile(
    int id, {
    String? businessName,
    String? businessDescription,
    String? sector,
    bool? isActive,
  }) async {
    try {
      await _service.updateBusinessProfile(
        id,
        businessName: businessName,
        businessDescription: businessDescription,
        sector: sector,
        isActive: isActive,
      );
      await loadBusinessProfiles();
    } catch (e) {
      // Error handling
    }
  }

  Future<void> deleteProfile(int id) async {
    try {
      await _service.deleteBusinessProfile(id);
      await loadBusinessProfiles();
    } catch (e) {
      // Error handling
    }
  }
}
