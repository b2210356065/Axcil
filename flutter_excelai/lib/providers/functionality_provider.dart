import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/functionality.dart';
import '../services/functionality_service.dart';

final functionalityServiceProvider = Provider((ref) => FunctionalityService());

final functionalityListProvider =
    FutureProvider.family<List<Functionality>, int>((ref, businessId) async {
  final service = ref.watch(functionalityServiceProvider);
  return await service.getFunctionalities(businessId);
});

final functionalityNotifierProvider = StateNotifierProvider.family<
    FunctionalityNotifier,
    AsyncValue<List<Functionality>>,
    int>((ref, businessId) {
  return FunctionalityNotifier(
    ref.watch(functionalityServiceProvider),
    businessId,
  );
});

class FunctionalityNotifier
    extends StateNotifier<AsyncValue<List<Functionality>>> {
  final FunctionalityService _service;
  final int businessId;

  FunctionalityNotifier(this._service, this.businessId)
      : super(const AsyncValue.loading()) {
    loadFunctionalities();
  }

  Future<void> loadFunctionalities() async {
    state = const AsyncValue.loading();
    try {
      final functionalities = await _service.getFunctionalities(businessId);
      state = AsyncValue.data(functionalities);
    } catch (e, stack) {
      state = AsyncValue.error(e, stack);
    }
  }

  Future<void> createFunctionality({
    required String name,
    required String description,
  }) async {
    try {
      await _service.createFunctionality(
        businessId: businessId,
        name: name,
        description: description,
      );
      await loadFunctionalities();
    } catch (e) {
      // Error handling
    }
  }

  Future<void> updateFunctionality(
    int id, {
    String? name,
    String? description,
  }) async {
    try {
      await _service.updateFunctionality(
        id,
        businessId: businessId,
        name: name,
        description: description,
      );
      await loadFunctionalities();
    } catch (e) {
      // Error handling
    }
  }

  Future<void> deleteFunctionality(int id) async {
    try {
      await _service.deleteFunctionality(id);
      await loadFunctionalities();
    } catch (e) {
      // Error handling
    }
  }

  Future<void> enrichFunctionality(int id) async {
    try {
      await _service.enrichFunctionality(id);
      await loadFunctionalities();
    } catch (e) {
      // Error handling
    }
  }
}
