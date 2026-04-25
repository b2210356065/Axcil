import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/api_config.dart';
import '../services/config_service.dart';

final configServiceProvider = Provider((ref) => ConfigService());

final configProvider = FutureProvider<ApiConfig>((ref) async {
  final service = ref.watch(configServiceProvider);
  return await service.getConfig();
});

final configNotifierProvider =
    StateNotifierProvider<ConfigNotifier, AsyncValue<ApiConfig>>((ref) {
  return ConfigNotifier(ref.watch(configServiceProvider));
});

class ConfigNotifier extends StateNotifier<AsyncValue<ApiConfig>> {
  final ConfigService _service;

  ConfigNotifier(this._service) : super(const AsyncValue.loading()) {
    loadConfig();
  }

  Future<void> loadConfig() async {
    state = const AsyncValue.loading();
    try {
      final config = await _service.getConfig();
      state = AsyncValue.data(config);
    } catch (e, stack) {
      state = AsyncValue.error(e, stack);
    }
  }

  Future<void> updateConfig(ApiConfig config) async {
    state = const AsyncValue.loading();
    try {
      final updated = await _service.updateConfig(config);
      state = AsyncValue.data(updated);
    } catch (e, stack) {
      state = AsyncValue.error(e, stack);
    }
  }
}
